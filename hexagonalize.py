#!/usr/bin/env python3
from PIL import Image
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
import numpy as np
import sys
from math import sqrt
from collections import defaultdict

#HEX_RADIUS = 4 # In pixels
HEX_RADIUS = 7 # In pixels
HEX_DIAMETER = HEX_RADIUS * 2
CUTOFF = 0.22
#CUTOFF = 0.27
DPI = 81

# Convert from QRS to pixel coordinates in matplotlib style
def cubeToCartesian(q,r,s):
	x = HEX_RADIUS * (sqrt(3) * q + sqrt(3)/2 * r)
	y = HEX_RADIUS * (3/2 * r)
	return (x,y)

# Convert from cartesian to cube coords, rounding to the containing hexagon
def cartesianToCube(x,y):
	basis = np.array([[sqrt(3)/3, -1/3],[0,2/3]])
	(q,r) = np.matmul(basis, [[x],[y]]).flatten() // HEX_RADIUS
	s = -1 * (q+r)
	return (int(q),int(r),int(s))

def plotHexagon(ax,q,r,s,color,edgecolor="blue"):
	(x,y) = cubeToCartesian(q,r,s)
	hex_ = RegularPolygon((x,y), numVertices=6, radius=HEX_RADIUS, orientation=np.radians(120), facecolor=color, alpha=1.0, edgecolor=edgecolor)
	ax.add_patch(hex_)

if __name__ == "__main__":
	img = Image.open("processed.png")
	pixels = np.array(img)
	# Of course matplotlib and PIL have differing coordinate systems,
	# but only in the y-axis
	mpl_pixels = pixels[::-1,::]
	height,width = pixels.shape

	# Plot the image with the hexagonal lattice overlaid
	fig,ax = plt.subplots(1)
	ax.set_axis_off()
	grays = mpl.colormaps["Greys"].reversed()
	ax.imshow(mpl_pixels, cmap=grays, interpolation="nearest", aspect="auto")
	hexes = defaultdict(lambda: [0,0])
	for y in range(0, height):
		for x in range(0, width):
			(q,r,s) = cartesianToCube(x,y)
			if( mpl_pixels[y,x] ):
				hexes[(q,r,s)][0] += 1
			else:
				hexes[(q,r,s)][1] += 1
	for (q,r,s) in hexes.keys():
		plotHexagon(ax,q,r,s,"None")
	ax.axis("off")
	ax.set_xlim(0, width)
	ax.set_ylim(0, height)
	plt.savefig("hexagons.png", bbox_inches="tight", pad_inches=0)
	plt.clf()

	# Now plot *only* the excavated hexagons
	fig,ax = plt.subplots(1)
	excavated = []
	ax.set_axis_off()
	for (q,r,s) in hexes.keys():
		(empty,filled) = hexes[(q,r,s)]
		ratio = filled / (empty+filled)
		#print("Tile (%d,%d,%d): %d filled, %d empty => %.2f filled" % (q,r,s,filled,empty,ratio))
		if( ratio > CUTOFF ):
			plotHexagon(ax,q,r,s,"k","k")
			excavated.append((q,r,s))
	ax.axis("off")
	ax.set_xlim(0, width)
	ax.set_ylim(0, height)
	plt.savefig("mapped.png", bbox_inches="tight", pad_inches=0)
	with open("mapped.csv", "w") as f:
		for (q,r,s) in excavated:
			f.write("%d,%d,%d\n" % (q,r,s))
