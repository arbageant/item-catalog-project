# Item Catalog
Author: Andrew Bageant\
Last Updated: 2019-04-08

## Introduction

This simple web application uses Flask and postgreSQL to maintain a simple
generic catalog of items, allowing users to add, update, and delete. It
leverages Google Signin for authorization and implements basic protections to
ensure that users can only edit items they create. The optimal environment to
run this app is the Ubuntu virtual machine available from Udacity, using vagrant.
You can find the VM on their github here:

https://github.com/arbageant/fullstack-nanodegree-vm

The app is configured to run out of the 'vagrant' directory in this VM.

A note about production: this app is currently configured for dev, and should
only be accessed at http://localhost:5000. The options on the server are NOT
currently configured for a production environment.

## Database Setup
This app will use a database titled itemcatalog as its backend. If you need to
initialize this database, run the following command in the VM:\
$ python database_setup.py

For testing purposes, I've provided a script that will populate the database
with some generic catalog items. You can execute this by running the following
command in the VM:\
$ python populate_data.py


A brief summary of the data:
The User table has a row for each unique user, along with an assigned ID and
the email acquired from Google Signin.

The Category table includes a row for each category, as well as a unique ID
and the user_id information for whoever created that category as a foreign key.

The Item table includes a row for each item, as well as a unique item ID. It
also contains the ID for the category the item belongs to, as well as the ID
of the user that created it (both as foreign keys).

## Running the App
To run the code, first use Vagrant to SSH into a virtual machine like the
one described in the introduction. Then, run the following:\
$ python application.py

You'll be able to connect to the catalog home page at the following URL:\
http://localhost:5000/catalog

## Using the App
You should be able to use the links within the app to view the items within
each different category, as well as create, edit, and delete items and
categories.

User authentication/authorization is handled with Google Signin, which you
can initiate using the 'Login' link on the home page. Note that only the user
who created a category/item should be permitted to edit/delete that category/item.

## Work in Progress
The core functionality of the app should work, but it's currently hideous.
This is because I'm an HTML noob and I'm trying to learn how to better utilize
HTML, CSS, and Javascript to make a decent looking web application. When I have
the opportunity, I'm going to spend some time improving the aesthetics of the
app. If you have any suggestions for good HTML learning resources, please let
me know!
