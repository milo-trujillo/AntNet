#!/usr/bin/env python3
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import igraph as ig
from enum import Enum

from hexagonalize import cubeToCartesian, cartesianToCube, plotHexagon

# Must have this many neighbors to continue flood-filling
NEIGHBOR_THRESHOLD = 4
MIN_JUNCTION = 4
MIN_ROOM = 10

ROOM_COLOR = "blue"
JUNCTION_COLOR = "red"
TUNNEL_COLOR = "k"

class State(Enum):
	UNEXPLORED = 1
	EXPLORED = 2
	ROOM = 3
	JUNCTION = 4
	TUNNEL = 5

def dfToExploreDict(df):
	toExplore = dict()
	for index,row in df.iterrows():
		coord = (row["q"], row["r"], row["s"])
		toExplore[coord] = State.UNEXPLORED
	return toExplore

# Returns a list of adjacent q,r,s coordinates, which may or may not exist in
# our graph
def getNeighbors(q,r,s):
	RELATIVE = [(-1,-1,0), (0,1,-1), (1,0,-1), (1,-1,0), (0,-1,1), (-1,0,1)]
	neighbors = [(q+n[0],r+n[1],s+n[2]) for n in RELATIVE]
	return neighbors

# Main flood-fill recursive function, keeps going so long as there are enough
# unexplored neighbors, returns a partition of connected tiles
def fill(q, r, s, tiles):
	if( tiles[(q,r,s)] != State.UNEXPLORED ):
		return []
	tiles[(q,r,s)] = State.EXPLORED
	space = [(q,r,s)]
	neighbors = getNeighbors(q,r,s)
	realNeighbors = [n for n in neighbors if n in tiles]
	if( len(realNeighbors) >= NEIGHBOR_THRESHOLD ):
		for n in realNeighbors:
			space += fill(*n, tiles)
	return space	

# Return a list of partitions obtained by flood-filling from each tile
def floodFill(tiles):
	partitions = []
	for tile in tiles:
		filled = fill(*tile, tiles)
		if( len(filled) > 0 ):
			partitions.append(filled)
	return partitions

# Identified whether partitions represent rooms, junctions, or tunnels, based
# on size. Returns the rooms and junctions as a tuple of lists
# ([rooms], [junctions])
def partitionsToCategories(partitions, tiles):
	def assignTiles(partition, tiles, category):
		for tile in partition:
			tiles[tile] = category
	rooms = []
	junctions = []
	for part in partitions:
		size = len(part)
		if( size >= MIN_ROOM ):
			assignTiles(part, tiles, State.ROOM)
			rooms.append(part)
		elif( size >= MIN_JUNCTION ):
			assignTiles(part, tiles, State.JUNCTION)
			junctions.append(part)
		else:
			assignTiles(part, tiles, State.TUNNEL)
	return (rooms,junctions)

def getMaxDimensions(tiles):
	maxX = 0
	maxY = 0
	for (x,y) in [cubeToCartesian(*tile) for tile in tiles]:
		maxX = max([x,maxX])
		maxY = max([y,maxY])
	return (maxX, maxY)

# Plots hexagonal lattice, with colors indicating room, junction, or tunnel
def plotLayout(tiles):
	(maxX,maxY) = getMaxDimensions(tiles)
	fig,ax = plt.subplots(1)
	ax.set_axis_off()
	ax.axis("off")
	for tile in tiles:
		(q,r,s) = tile
		if( tiles[tile] == State.ROOM ):
			plotHexagon(ax,q,r,s,ROOM_COLOR)
		elif( tiles[tile] == State.JUNCTION ):
			plotHexagon(ax,*tile,JUNCTION_COLOR)
		elif( tiles[tile] == State.TUNNEL ):
			plotHexagon(ax,*tile,TUNNEL_COLOR)
	ax.set_xlim(0, maxX)
	ax.set_ylim(0, maxY)
	plt.savefig("floodfilled.png", bbox_inches="tight", pad_inches=0)
	plt.clf()

def generateGraph(vertexClusters, tiles):
	g = ig.Graph()
	for cluster in vertexClusters:
		Xs, Ys = [], []
		for (x,y) in [cubeToCartesian(*tile) for tile in cluster]:
			Xs.append(x)
			Ys.append(y)
		avgX = np.median(Xs)
		avgY = np.median(Ys)
		category = tiles[cluster[0]]
		color = None
		if( category == State.ROOM ):
			color = ROOM_COLOR
		else:
			color = JUNCTION_COLOR
		g.add_vertex(x=avgX, y=avgY, size=len(cluster), category=category, color=color)
	return g

def plotGraph(g, tiles):
	(maxX, maxY) = getMaxDimensions(tiles)
	fig, ax = plt.subplots()
	ax.set_axis_off()
	ax.axis("off")
	def normalizeSize():
		return [s/2 for s in g.vs["size"]]
	ig.plot(g, target=ax, vertex_size=normalizeSize(), vertex_color=g.vs["color"])
	plt.savefig("graph.png", bbox_inches="tight", pad_inches=0)
	plt.clf()

if __name__ == "__main__":
	df = pd.read_csv("mapped.csv", header=None, names=["q", "r", "s"])
	tiles = dfToExploreDict(df)
	partitions = floodFill(tiles)
	(rooms,junctions) = partitionsToCategories(partitions, tiles)
	plotLayout(tiles)
	g = generateGraph(rooms+junctions, tiles)
	plotGraph(g,tiles)
