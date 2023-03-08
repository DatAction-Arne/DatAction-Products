# DatAction-Products

### Deploy instructions

Open a Git Bash and send the following commands to deploy the project to the cloud:
````
eval $(ssh-agent)
ssh-add ~/.ssh/ssh-key
ssh-add -l
git add.
git commit -m "<name>"
git push -u webpaas master
````

To update the poetry lock file:
````
poetry lock --no-update
````