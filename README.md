# Sigmar's Garden Auto-Solver

After 75 games I decided I was done with the game, even if Anataeus wasn't yet. I wanted to see the story, since I'm shipping Anataeus and Concordia, so I wrote this crappy little solver.

> "Works on my machine!"
> 
> _Quality Gauruntee_

_Please note: low quality code indicative of weekend work only, can not be used to judge my professional competency, may cause cancer in the state of California_

## Requirements

* OS: Should work on Windows, might work otherwise?
* Python, 3, of course, and pip
* Game is on primary monitor
* Only starts from fresh games, not partially solved games

## Installation

```bash
git clone whatever whatever
cd whatever
# Make whatever virtualenv you want, if you care
pip install -r requirements.txt
```

## Usage

* Start the game, make sure it's running on the primary monitor or pyautogui will be sad
* `python ./sigmar.py --n_games=1`
* Then:
    * It will look for the game window
    * Solve the game (outputting states in the console)
        * Most games solve in under a second, some rare ones take a minute or more!
    * Click once in the top-left to ensure the game has focus
    * Click to solve the game
    * Click 'New Game' and wait for the board to populate

Or maybe it'll just error out.

If clicking seems funky, try adding the arg `--slow True`

Use more `--n_games` if you want it to solve a bunch in a row.

## How it works

pyautogui for operating the mouse and screenshotting.

skimage.metrics.structural_similarity for turning marble images into a model

A simple depth-first search for exploring the game states. No heuristic for trying to play optimally like what one would use for an A*. 

