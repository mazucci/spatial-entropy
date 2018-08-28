################################################################################
# Copyright 2018 Mayra Zurbaran 
# Modified from Ujaval Gandhi 2014
#
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
################################################################################
from qgis.utils import iface
from PyQt4.QtCore import QVariant
from collections import Counter
import math

# Replace the values below with values from your layer.
# For example, if your identifier field is called 'XYZ', then change the line
# below to _NAME_FIELD = 'XYZ'
_NAME_FIELD = "Eqid"
# Replace the value below with the field name that you want to use to calculate entropy.
# For example, if the # field that you want to sum up is called 'VALUES', then
# change the line below to _ENT_FIELD = 'VALUES'
_ENT_FIELD = "Magnitude"
_NEW_NEIGHBORS_FIELD = 'NEIGHBORS'
_NEW_ENT_FIELD = 'ENTROPY'

layer = iface.activeLayer()

# Create 2 new fields in the layer that will hold the list of neighbors and entropy
# of the chosen field.
layer.startEditing()
layer.dataProvider().addAttributes(
        [QgsField(_NEW_NEIGHBORS_FIELD, QVariant.String),
         QgsField(_NEW_ENT_FIELD, QVariant.Double)])
layer.updateFields()
# Create a dictionary of all features
feature_dict = {f.id(): f for f in layer.getFeatures()}

# Build a spatial index
index = QgsSpatialIndex()
for f in feature_dict.values():
    index.insertFeature(f)

for f in feature_dict.values():
    print 'Working on %s' % f[_NAME_FIELD]
    geom = f.geometry()
    # Find all features that intersect the bounding box of the current feature.
    # We use spatial index to find the features intersecting the bounding box
    # of the current feature. This will narrow down the features that we need
    # to check neighboring features.
    intersecting_ids = index.intersects(geom.boundingBox())
    # Initalize neighbors list and sum
    neighbors = []
    neighbors_ent = []
    for intersecting_id in intersecting_ids:
        # Look up the feature from the dictionary
        intersecting_f = feature_dict[intersecting_id]

        # For our purpose we consider a feature as 'neighbor' if it touches or
        # intersects a feature. We use the 'disjoint' predicate to satisfy
        # these conditions. So if a feature is not disjoint, it is a neighbor.
        if (f != intersecting_f and not intersecting_f.geometry().disjoint(geom)):
            neighbors.append(intersecting_f[_NAME_FIELD])
            neighbors_ent.append(int(intersecting_f[_ENT_FIELD]))
    #calculate frequency of this neighborhood
    neighbor_frqs = Counter(neighbors_ent)
    #init entropy sum -- entropy = (-1)*sum(p*log(p))
    _ent = 0.0
    for val in neighbors_ent:
        #Get the frecuency of this val, then we use it to calculate probability
        p_val = neighbor_frqs[val]/float(len(neighbors))
        #Sum of each
        _ent += p_val*math.log(p_val, 2.0)

    f[_NEW_NEIGHBORS_FIELD] = ','.join(neighbors)
    #multiply by the constant (-1)
    f[_NEW_ENT_FIELD] = _ent*-1
    # Update the layer with new attribute values.
    layer.updateFeature(f)

layer.commitChanges()
print 'Processing complete.'
