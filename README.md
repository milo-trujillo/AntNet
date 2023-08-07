## AntNet

This code takes a photo of an ant farm and attempts to convert it to a network diagram. It's a clumsy toy project, [discussed in detail here.](https://backdrifting.net/post/070_antnet)

To try it out, first get a photo of an ant farm - we'll call it `ants.png`. Then, run:

```
./preprocess ants.png processed.png
./hexagonalize.py
./floodfill.py
./montage.sh
```

### Dependencies

Requires ImageMagick, and the following Python packages:

    pip3 install igraph matplotlib seaborn pandas numpy PIL
