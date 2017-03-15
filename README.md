## Motivation

Initially a python module (`sppas_tool.py`) to [choose between various versions](#sppas_toolpy--switch-between-various-sppas-versions) of [SPPAS](http://www.sppas.org/) (useful to test new developments).

Then a couple of scripts for varied tasks :
 - [showing basic information](#sppas_infopy--show-basic-information-about-annotation-files) about annotation files
 - [CSV extraction](#sppas_fb2csvpy--extract-a-tier-into-a-csv-file)
 - [merge tiers from various files](#sppas_mergepy--merge-andor-reorder-tiers-from-various-files)
 - [boundaries/BILOU annotation](#sppas_boundariespysppas_biloupy--create-boundaries-or-bilou-representations-of-annotations)
 - [some statistics](#sppas_stats2py--some-statistics-measures)

## Synopsis

All scripts share the options offered by `sppas_tool.py` to choose the SPPAS installation (see [first section](#sppas_toolpy--switch-between-various-sppas-versions)).
<br>Scripts have generally the `--help` (or `-h`) option that shows a brief description.
 

### sppas_tool.py : switch between various SPPAS versions

`sppas_tool.py` offers 4 ways to define the SPPAS installation used to run the script (and the others script in this repository).

1. Define the directory path with the command line option `--sppas-dir` or `-D`

  ```sh
  python sppas_tool.py --sppas-dir /path/to/sppas-version
  # OR
  python sppas_tool.py -D /path/to/sppas-version
  ```

2. Define the directory path with the environment variable `SPPAS_DIR`

  ```sh
  SPPAS_DIR=/path/to/sppas-version python sppas_tool.py
  # OR
  export SPPAS_DIR=/path/to/sppas-version
  python sppas_tool.py
  ```

3. Define the version with the command line option `--sppas-version` or `-V`
  
  ```sh
  python sppas_tool.py --sppas-version 1.8.2
  # OR
  python sppas_tool.py -V 1.8.2
  ```
  
  The current version of `sppas_tool.py` only look for SPPAS inside the directory `<home>/bin/sppas-<version>`.
  Perhaps a further version will look inside more directories.

4. Define the version with the environment variable `SPPAS_VERSION`

  ```sh
  SPPAS_VERSION=1.8.2 python sppas_tool.py
  # OR
  export SPPAS_VERSION=1.8.2
  python sppas_tool.py
  ```
  
  Like said in the previous point, `sppas_tool.py` look for SPPAS inside the directory `<home>/bin/sppas-<version>`.

This 4 ways are presented in the order of priority.
By example `SPPAS_DIR=/path/to/sppas-1.7.9 python sppas_tool.py -V 1.8.3` will use SPPAS defined by `SPPAS_DIR` (`/path/to/sppas-1.7.9`) and ignore the command line version option (`<home>/bin/sppas-1.8.3`).
<br>Nota: in last resort, `sppas_tool.py` use `1.7.7` as the default version.

`sppas_tool.py` per se didn't do nothing, except print some informations on the chosen SPPAS installation - which allow to check if you use the good directory/version parameter for running the others script.
By example, an output for `python sppas_tool.py` with the environment variable `SPPAS_VERSION=1.8.2` look like:
```txt
Parsed options are : Namespace(sppas_dir=None, sppas_version=None)
Use environment variable SPPAS_VERSION:1.8.2
Use SPPAS directory:/home/me/bin/sppas-1.8.2
SPPAS is loaded from: '/home/me/bin/sppas-1.8.2' (real path: '/home/me/bin/sppas-1.8.2')
```

Nota: `sppas_tool.py` offers also some methods used by the others scripts... more details will come (soon?).

### sppas_info.py : show basic information about annotation files

`sppas_info.py` shows some basic information about annotation files (supported by SPPAS) :
 - number of tiers
 - list of tiers
 - Min/Max times

```sh
python sppas_info.py APraatFile.TextGrid AnELANFile.eaf
```
Print something like :
```txt
[APraatFile.TextGrid] Loading annotation file...
[APraatFile.TextGrid] Number of tiers: 7
[APraatFile.TextGrid] Tiers are :
   [0] 'P1_IPU', [1] 'P1_Tokens', [2] 'P1_Feedbacks', [3] 'P2_IPU'
   [4] 'P2_Tokens', [5] 'P2_Feedbacks', [6] 'Script' 
[APraatFile.TextGrid] Min/Max times: [ 0.0 ; 937.985 ]
[AnELANFile.eaf] Loading annotation file...
[AnELANFile.eaf] Number of tiers: 9
[AnELANFile.eaf] Tiers are :
   [0] 'P1_IPU', [1] 'P1_Tokens', [2] 'P1_Feedbacks', [3] 'P2_IPU'
   [4] 'P2_Tokens', [5] 'P2_Feedbacks', [6] 'Script', [7] 'P1_Gesture'
   [8] 'P2_Gesture'
[AnELANFile.eaf] Min/Max times: [ 0.0 ; 937.985 ]
````

### sppas_fb2csv.py : extract a tier into a CSV file

Extract one tier of one or various files into a CSV file.
<br/>Output file(s) are named with the name of the file without extension and the tier name.

```sh
python sppas_fb2csv.py -t P1_Tokens projectA/APraatFile.TextGrid projectB/AnELANFile.eaf
```

Produce 2 CSV files `projectA/APraatFile-P1_Tokens.csv` and `projectB/AnELANFile-P1_Tokens.csv`.

### sppas_merge.py : merge (and/or reorder) tiers from various files

Merge the tiers of various files in a single one.
<br/>Options allow to reorder the tiers in the output file and exclude some tiers.

Basic usage : merge various files (of various formats).
```sh
python sppas_merge.py FirstFile.eaf SecondFile.TextGrid ThirdFile.eaf --outfile MergedFile.eaf
```

The ```--first-tiers``` options (short ```-t```) give the (list of) tiers to place first, which allow **reorder** the tiers.
<br/>You can pass a list of tier's names separated by comma:
```sh
python sppas_merge.py FirstFile.eaf SecondFile.TextGrid --first-tiers VIPTier,ImportantTier,ThirdTier --outfile MergedFile.eaf
```
And/or repeat the  ```--first-tiers``` option:
```sh
# Equivalent to 
python sppas_merge.py FirstFile.eaf SecondFile.TextGrid -t VIPTier -t ImportantTier -t ThirdTier --outfile MergedFile.eaf
# Or
python sppas_merge.py FirstFile.eaf SecondFile.TextGrid -t VIPTier,ImportantTier -t ThirdTier --outfile MergedFile.eaf
```

In a similar way, you can **exclude** some tier(s) with the ```--exclude-tiers``` option (short ```-x```):
```sh
python sppas_merge.py FirstFile.eaf SecondFile.TextGrid -x NobodyTier,HasBeenTier --exclude-tiers UselessTier --outfile MergedFile.eaf
```

In the case of **duplicated tier names**, i.e. two or more tiers having the same name in various files, the *current strategy* is to keep the first one and ignore the folowing ones. So the order of the input files is important.

As the tier names are not always folowing a strict uppercase/lowercase convention, the ```--ignore-case``` option (short ```-i```) allow to use case insensitive matching in all tier names research (duplicate, reorder and exclusion).


### sppas_boundaries.py/sppas_bilou.py : create boundaries or BILOU representations of annotations

This two scripts comes from the necessity to compare the delimitations produced by differents annotators - with a tolerance for the boundaries time points.

They offers two approaches: 
  - *BILOU* create a *base time* subdivision, i.e. regular intervals (of 100ms by default),
    and fill the intervals with the corresponding *BILOU* tags (*BILOU* stands for **B**egin, **I**n, **L**ast, **O**utside and **U**nit).
    <br/>Example:
    
    ```txt
       ref =       [------]   [---] [----]    []   [-----]   [] [---------]
       base= |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
        =>   | O | B | I | L | B |L+B| L | O | U | B | L | O |U+B| I | I | L |
    ```

    So, the comparaison of the boundaries (and overlaps) of two annotations is easier on the *BILOU* tiers.
    ```txt
        an1 =       [------]   [---] [----]    []   [-----]   [] [---------]
        an2 =       [-----]    [---]  [---]    [-]   [----]   []  [--------]
      bilou1= | O | B | I | L | B |L+B| L | O | U | B | L | O |U+B| I | I | L |
      bilou2= | O | B | L | 0 | B | L | U | O | U | B | L | O | U | B | I | L |
      eq1-2 = | O | B |   |   | B | L~|   | O | U | B | L | O | U~|   | I | L |
    ```
  
  - *boundaries*, in contrast, doesn't requiere a base time subdivision as it *reuses the boundaries time points* and attach **B**egin/**E**nd tag.
    <br/>By default it create a tier of time points:
    
    ```txt
       ref =       [--1---]     [-2--]   [--3--]     [4]     [--5--]
        =>         B      E     B    E   B     E     B E     B     E
    ```
    
    But can also transform them into intervals:
    
    ```txt
       ref =       [--1---]     [-2--]   [--3--]     [4]     [--5--]
        =>       [ B ]  [ E ] [ B ][ E | B ] [ E ] [ B|E ] [ B ] [ E ]
    ```
    nota: In the case of intervals, sometime they are shorter to avoid overlap, like between [2] and [3] or inside [4]

    So, we can compare the boundaries of various annotations.
    ```txt
        an1 =       [------]   [---] [----]    []   [-----]   [] [---------]
        an2 =       [-----]    [-----] [--]    [-]   [----]   []  [--------]
      bound1=       B      E   B   E B    E    BE   B     E   BE B         E
      bound2=       B     E    B     E B  E    B E   B    E   BE  B        E
      eq1-2 =       B          B     H    E    B          E   BE           E
    ```
    nota: the "H" point in "eq1-2" is a point with *same time* but distinct labels.

#### BILOU usage

Create the *BILOU* tiers of two tiers with a *base time* of 500ms:
```sh
python sppas_bilou.py --tier an1 --tier an2 --base 0.5 MyAnnotFile.eaf 
```
Produce an output file, named ```MyAnnotFile-BILOU_an1+an2.eaf``` (see ```--outfile-format``` option), with the input tiers of ```MyAnnotFile.eaf``` plus two *BILOU* tiers, named with the original tier name and the base time value, in this case "BILOU - an1 - 0.500s" and "BILOU - an2 - 0.500s" (see ```--bilou-tier-format``` options).

By default the *outside* label is an empty label and the *BILU* labels are composed of the first letter (B, I, L, or U).
By example :
```txt
 ref =       [---a---]         [---b---]         [-a-]        [--b--]    [c]         [-----a------]
  =>   |     |  B  |  L  |    |  B  |  L  |     |  U  |     |  B  |  L  |  U  |     |  B  |  I  |  L  |
```

The option ```--o-label``` change the value of the *outside* label and ```--bilu-format``` the format of the *BILU* labels, combining the *BILU* name (first field) with the original label (second field).
<br/>Some example of the possibilities of the *BILU* format option:
```txt
    ref    =       [---a---]         [---b---]         [-a-]        [--b--]    [c]         [-----a------]
{:.1}      = |     |  B  |  L  |    |  B  |  L  |     |  U  |     |  B  |  L  |  U  |     |  B  |  I  |  L  |
{}         = |     |Begin|Last |    |Begin|Last |     |Unit |     |Begin|Last |Unit |     |Begin| In  |Last |
{:.1}({})  = |     |B(a) |L(a) |    |B(b) |L(b) |     |U(a) |     |B(b) |L(b) |U(c) |     |B(a) |I(a) |L(a) |
{1:}_{0:.1}= |     | a_B | a_L |    | b_B | b_L |     | a_U |     | b_B | b_L | c_U |     | a_B | a_I | a_L |
```

Finnally, with the ```--keep``` option, it is possible to restrict the tiers in the output file(s), either to the processed tiers and resulting *BILOU* tiers (```--keep process```) or simply to the resulting *BILOU* tiers (```--keep bilou```).

#### bondaries usage

```sppas_boundaries.py``` is very similar to ```sppas_bilou.py```.
<br/>Create the *boundaries* tiers of three tiers:
```sh
python sppas_boundaries.py --tier an1 --tier an2 --tier an3 MyAnnotFile.eaf 
# OR, to obtain intervals
python sppas_boundaries.py --intervals --tier an1 --tier an2 --tier an3 MyAnnotFile.eaf 
```
This produce an output file, named ```MyAnnotFile-bound_an1+an2+an3.eaf``` (see ```--outfile-format``` option), with the input tiers of ```MyAnnotFile.eaf``` plus three *boundaries* tiers, named with the original tier name, in this case "Boundaries - an1", "Boundaries - an2" and "Boundaries - an3" (see ```--bound-tier-format``` options).

With the option ```--equals-tier```, the script also calculates the __*equals* tiers__.
<br/>The *equals* tiers are tiers that keep the points occuring at the *same time* in 2 tiers (see the "eq1-2" example before), independently of their label (like the "H" point in the example).
<br/>Like in SPPAS, to occur at the __*same time*__, two time points don't require to have the exact same numeric value, but should overlap considering their __*radius*__.
<br/>By exemple, if we consider two time points, respectively A=1.234s and B=1.333s.
If the radius of the two points is only 40ms (one image at a 25 frame/s rate), the two points are similar to the intervals A1=[1.194, 1.274] and B1=[1.293, 1.373], so their are distinct.
But if the radius of the two points is 80ms (two images), the two points are similar to the intervals A2=[1.154, 1.314] and B1=[1.253, 1.413], so their are considered the *same time*.
<br/>So the *radius* is very important for the *equals* relation, you can change it with the option ```--radius``` ((!) in second, not millisecond).
<br/>By default the radius option is a negative value, in which case the script use the radius attached to the original tier (in the few formats that support radius, like SPPAS's XRA) or the SPPAS default value (0.0005, i.e. 0.5ms).

```sh
python sppas_boundaries.py --tier an1 --tier an2 --tier an3 --equals-tier --radius 0.100 MyAnnotFile.eaf 
```
This add to the previous output the two *equality* tiers that compare the first tier "an1" to the other ones: "Boundaries an1 VS an2" and "Boundaries an1 VS an3" (see ```--equals-tier-format``` option for the name).

As for the *BILOU* script, it's possible to customize the labels on the *boundaries* (options ```--begin-format``` and  ```--end-format```) and *equals* tiers (option ```--equals-label-format```).

The ```--keep``` option has the same effect (the value "boundaries" replace "bilou").


### sppas_stats2.py : some statistics measures

```sppas_stats2.py``` is the main *cause* of [sppas_tool.py](#sppas_toolpy--switch-between-various-sppas-versions) as I worked to add a new set of relations between the annotations, based on the delay between the start and/or end points ([delay relations](http://www.sppas.org/manual/sppas.src.annotationdata.filter.delay_relations-module.html) were merged in the version 1.7.7 of SPPAS).

It's too long to explain what compute ```sppas_stats2.py```, I let it in this repository as it could be instructive to look inside the script.
<br/>The *statistics* measures serve us in the context of the [ACORFORMED](http://www.lpl-aix.fr/~acorformed/) project.

## Installation

Every scripts require `sppas_tool.py` in the search path for modules (`sys.path`) - basically copy it in the same directory -
<br/> and an version of [SPPAS](http://www.sppas.org/) (at least between 1.7.7 and 1.8.3, but we recommand the last version).

## License

These sample scripts can be considered as *public-domain*.

But, as when you use them **you also use SPPAS**, don't forgive the terms of the **[GPL version 3 licence](https://www.gnu.org/licenses/gpl-3.0.en.html)** and the recommendation to **cite a reference in your publication**, like here :

        Brigitte BIGI (2015).
        SPPAS - Multi-lingual Approaches to the Automatic Annotation of Speech.
        The Phonetician - International Society of Phonetic Sciences,
        ISSN 0741-6164, Number 111-112 / 2015-I-II, pages 54-69.

Details on the SPPAS licence and references can be found [in the online documentation](http://www.sppas.org/documentation_07_references.html) or in the [GitHub page](https://github.com/brigittebigi/sppas).
