# Notes about the API

Here I document my findings about the API during my reverse engineering efforts.

# https://www.abfallplus.de/fuer-buerger/

```
- f_wkey: fc6451bcaedf0696047ff9e78b48309d
- fapi: 3e8fbf4dd972b642839dee3d5eb1c8bc


- Baden-Württemberg: c4ca4238a0b923820dcc509a6f75849b
- Bayern: c81e728d9d4c2f636f067f89cc14862c
- Berlin: eccbc87e4b5ce2fe28308fd9f2a7baf3
- Brandenburg: a87ff679a2f3e71d9181a67b7542122c
- Bremen: e4da3b7fbbce2345d7772b0674a318d5
- Hamburg: 1679091c5a880faf6fb5e6087eb1b2dc
- Hessen: 8f14e45fceea167a5a36dedd4bea2543
- Mecklenburg-Vorpommern: c9f0f895fb98ab9159f51fd0297e236d
- Niedersachsen: 45c48cce2e2d7fbdea1afc51c7c6ad26
- Nordrhein-Westfalen: d3d9446802a44259755d38e6d163e820
- Rheinland-Pfalz: 6512bd43d9caa6e02c990b0a82652dca
- Saarland: c20ad4d76fe97759aa27a0c99bff6710
- Sachsen: c51ce410c124a10e0db5e4b97fc2af39
- Sachsen-Anhalt: aab3238922bcc25a6f606eb525ffdc56
- Schleswig-Holstein: 9bf31c7ff062936a96d3c8bd1f8f2ff3
- Thüringen: c74d97b01eae257e44aa9d5bade97baf
```

```sh
# List of 
curl -X POST \
     -F f_wkey=fc6451bcaedf0696047ff9e78b48309d \
     -F f_id_bundesland=c4ca4238a0b923820dcc509a6f75849b \
     https://www.abfallplus.de/\?fapi\=3e8fbf4dd972b642839dee3d5eb1c8bc\&waction\=auswahl_bundesland_set
```
