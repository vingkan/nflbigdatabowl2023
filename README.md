# NFL Big Data Bowl 2023

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/vingkan/nflbigdatabowl2023/)

## Common Commands

| Command | Description |
|:--|:--|
| `pytest` | Run all unit tests. |
| `git checkout -b branch_name` | Create a new branch named `branch_name`. |
| `git status` | Check which files have been modified or added. |
| `git add .` | Add all changes. |
| `pre-commit run` | Run pre-commit on added changes. |
| `git commit -m  "message"` | Create a commit with a message and run pre-commit. |
| `git push` | Push changes to remote. |

## Setup Instructions

1. Accept the GitHub invitation granting you read and write access to this repository
2. [Login to GitPod](https://www.gitpod.io/) using the same GitHub account
3. [Login to Kaggle](https://www.kaggle.com/) and get your Kaggle credentials
    - Click on your profile picture in the top right corner and go to the "Your Profile" page
    - Click the "Account" tab
    - Scroll down to the "API" section
    - Click the "Create New API Token" button, which will trigger a download
    - Save the file to your computer
    - Open the file in a text editor to view your username and secret key
4. Go back to GitPod to save your Kaggle credentials
    - Open the [environment variables](https://gitpod.io/variables) page
    - Click the "New Variable" button
    - Create a new variable for your Kaggle username:
        - Name: `KAGGLE_USERNAME`
        - Value: `your_username`
        - Scope: `vingkan/nflbigdatabowl2023`
    - Create a new variable for your Kaggle key:
        - Name: `KAGGLE_KEY`
        - Value: `your_key`
        - Scope: `vingkan/nflbigdatabowl2023`
5. Go to [the GitHub repository page](https://github.com/vingkan/nflbigdatabowl2023) and click the GitPod button at the top of the README to start up a workspace
6. Automatic setup commands will run on GitPod and then you can use the terminal an editor freely
