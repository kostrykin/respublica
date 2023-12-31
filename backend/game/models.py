from django.core.exceptions import PermissionDenied
from django.db import models
import numpy as np

from world import hexgrid
from game.blueprints import base_blueprints


class Empire(models.Model):

    name      = models.CharField(max_length = 100, unique = True)
    player    = models.OneToOneField('auth.User', on_delete = models.SET_NULL, null = True)
    origin_x  = models.IntegerField();
    origin_y  = models.IntegerField();
    color_hue = models.FloatField()

    class Meta:
        constraints = (
            models.CheckConstraint(
                check = models.Q(color_hue__gte = 0) & models.Q(color_hue__lte = 1),
                name = 'color_hue_range'),
            )

    @property
    def origin(self):
        return np.asarray((self.origin_x, self.origin_y), dtype=int)

    @property
    def habitated_sectors(self):
        from world.models import Sector
        return Sector.objects.filter(celestial__habitated_by = self.id)

    @property
    def territory(self):
        atoms = list()
        for sector in self.habitated_sectors:
            atom = hexgrid.DistanceSet(center = sector.position, radius = 1)
            atoms.append(atom)
        return hexgrid.Union(atoms)

    def save(self, *args, **kwargs):
        is_newly_created = not self.pk
        super(Empire, self).save(*args, **kwargs)

        # If the empire is newly created, then also create its base blueprints
        if is_newly_created:
            for bp_type in base_blueprints.keys():
                for bp_name, bp in base_blueprints[bp_type].items():
                    Blueprint.objects.create(
                        base_id = f'{bp_type}/{bp_name}',
                        empire  = self,
                        data    = {key: bp[key] for key in ['name', 'cost', 'size', 'speed'] if key in bp})

    @property
    def movables(self):
        from world.models import Movable
        return Movable.objects.filter(ship__blueprint__empire = self).all()

    @property
    def ships(self):
        return Ship.objects.filter(blueprint__empire = self).all()


class Blueprint(models.Model):

    base_id = models.CharField(max_length = 100)
    empire  = models.ForeignKey('Empire', on_delete = models.CASCADE)
    data    = models.JSONField()

    @property
    def base(self):
        bp_type, bp_name = self.base_id.split('/')
        return base_blueprints[bp_type][bp_name]

    @property
    def requirements(self):
        return self.base.get('requirements', list())

    def requirements_ok(self, celestial):
        if celestial.habitated_by != self.empire:
            raise PermissionDenied()
        if celestial.remaining_capacity < self.data.get('size', 0):
            return False
        for requirement in self.requirements:
            if celestial.construction_set.filter(blueprint__base_id = requirement).count() == 0:
                return False
        return True

    def build(self, celestial):
        if not self.requirements_ok(celestial): return None
        from processes.models import BuildingHandler
        from world.models import World
        return BuildingHandler.create_process(World.objects.get().now, self, celestial)


class Construction(models.Model):

    blueprint = models.ForeignKey('Blueprint', on_delete = models.PROTECT)
    celestial = models.ForeignKey('world.Celestial', on_delete = models.CASCADE)


class Ship(models.Model):

    blueprint = models.ForeignKey('Blueprint', on_delete = models.PROTECT)
    movable   = models.ForeignKey('world.Movable', on_delete = models.PROTECT)

    @property
    def owner(self):
        return self.blueprint.empire

    @property
    def type_id(self):
        return self.blueprint.base_id

    @property
    def type(self):
        return self.blueprint.data['name']
