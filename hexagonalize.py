#!/usr/bin/env python3
from PIL import Image
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
import seaborn as sns
import pandas as pd
import numpy as np
import sys
from math import sqrt
from collections import defaultdict

#HEX_RADIUS = 4 # In pixels
HEX_RADIUS = 6 # In pixels
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

def getClosestValue(ratio):
	if( ratio > 0.5 ):
		return 1
	return 0

# Every hexagon should have three unevaluated neighbors for us to distribute
# error between - except hexagons at the edge of the board, where we'll let
# the error vanish
def addAdjacentError(q,r,s,error,hexes):
	#neighbors = [(0,-1,1), (1,-1,0), (1,0,-1)]
	neighbors = [(-1,1,0), (0,1,-1), (1,0,-1)]
	absolute_neighbors = [(n[0]+q,n[1]+r,n[2]+s) for n in neighbors]
	local_error = error / 3
	for n in absolute_neighbors:
		if n in hexes.keys():
			hexes[n][2] += local_error

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
	hexes = defaultdict(lambda: [0,0,0])
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
	og_ratios = []
	adapted_ratios = []
	errored_ratios = []
	ax.set_axis_off()
	for (q,r,s) in hexes.keys():
		(empty,filled,error) = hexes[(q,r,s)]
		raw_ratio = filled / (empty+filled)
		og_ratios.append(raw_ratio)
		raw_ratio = min([raw_ratio / 0.45, 1.0])
		adapted_ratios.append(raw_ratio)
		ratio = raw_ratio + error
		errored_ratios.append(ratio)
		#print("Tile (%d,%d,%d): %d filled, %d empty => %.2f filled" % (q,r,s,filled,empty,ratio))
		value = getClosestValue(ratio)
		round_error = value - ratio
		print("(%d,%d,%d) Raw ratio %.2f w/ error %.2f and round-error %.2f => %d" % (q,r,s,raw_ratio,error,round_error,value))
		#if( ratio > CUTOFF ):
		if( value == 1 ):
			plotHexagon(ax,q,r,s,"k","k")
			excavated.append((q,r,s))
		if( q == 0 and r == 0 and s == 0 ):
			plotHexagon(ax,q,r,s,"red","k")
		addAdjacentError(q,r,s,round_error,hexes)
	ax.axis("off")
	ax.set_xlim(0, width)
	ax.set_ylim(0, height)
	plt.savefig("mapped.png", bbox_inches="tight", pad_inches=0)
	plt.clf()
	df = pd.DataFrame({"original": og_ratios, "adapted": adapted_ratios, "dithered": errored_ratios})
	df = pd.melt(df, value_vars=["original", "adapted", "dithered"], var_name="Stage", value_name="Hexagonal Pixel Density")
	#sns.histplot(data=df, x="Hexagonal Pixel Density", hue="Stage")
	sns.kdeplot(data=df, x="Hexagonal Pixel Density", hue="Stage")
	plt.savefig("ratios.png", bbox_inches="tight")
	with open("mapped.csv", "w") as f:
		for (q,r,s) in excavated:
			f.write("%d,%d,%d\n" % (q,r,s))
