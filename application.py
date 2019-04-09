from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import requests
import json
from flask import make_response

app = Flask(__name__)

#Connect to Database and create database session
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

#Show category home
@app.route('/')
@app.route('/catalog')
def showCatalog():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    categories = session.query(Category).order_by(asc(Category.name))
    return render_template('catalog.html', categories = categories)

#Create a new category
@app.route('/catalog/new/', methods=['GET','POST'])
def newCategory():
  if request.method == 'POST':
      #if 'username' not in login_session:
          #return redirect('/login')
      DBSession = sessionmaker(bind=engine)
      session = DBSession()
      newCategory = Category(name = request.form['name'])
      session.add(newCategory)
      flash('New Category %s Successfully Created' % newCategory.name)
      session.commit()
      return redirect(url_for('showCatalog'))
  else:
      return render_template('newCategory.html')

#Edit a category
@app.route('/catalog/<int:category_id>/edit/', methods = ['GET', 'POST'])
def editCategory(category_id):
    #if 'username' not in login_session:
        #return redirect('/login')
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    editedCategory = session.query(Category).filter_by(id = category_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            session.add(editedCategory)
            session.commit()
            flash('Successfully Edited Category %s' % editedCategory.name)
            return redirect(url_for('showCatalog'))
    else:
        return render_template('editCategory.html', category = editedCategory)


#Delete a category
@app.route('/catalog/<int:category_id>/delete/', methods = ['GET','POST'])
def deleteCategory(category_id):
    #if 'username' not in login_session:
        #return redirect('/login')
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    categoryToDelete = session.query(Category).filter_by(id = category_id).one()
    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.commit()
        flash('%s Successfully Deleted' % categoryToDelete.name)
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteCategory.html',category = categoryToDelete)

#Show items in a category
@app.route('/catalog/<int:category_id>/')
@app.route('/catalog/<int:category_id>/items/')
def showItems(category_id):
    #if 'username' not in login_session:
        #return redirect('/login')
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).filter_by(id = category_id).one()
    items = session.query(Item).filter_by(category_id = category_id).all()
    return render_template('items.html', items = items, category = category)

#Show an individual item
@app.route('/catalog/<int:category_id>/items/<int:item_id>')
def showOneItem(category_id, item_id):
    #if 'username' not in login_session:
        #return redirect('/login')
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).filter_by(id = category_id).one()
    item = session.query(Item).filter_by(id = item_id).one()
    return render_template('oneItem.html', item = item, category = category)

#Create a new item in a category
@app.route('/catalog/<int:category_id>/items/new',methods=['GET','POST'])
def newItem(category_id):
    #if 'username' not in login_session:
        #return redirect('/login')
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).filter_by(id = category_id).one()
    if request.method == 'POST':
        newItem = Item(name = request.form['name'], description = request.form['description'], category_id = category_id)
        session.add(newItem)
        session.commit()
        flash('New Item %s Successfully Created' % (newItem.name))
        return redirect(url_for('showItems', category_id = category_id))
    else:
        return render_template('newItem.html', category_id = category_id)

#Edit an item in this category
@app.route('/catalog/<int:category_id>/items/<int:item_id>/edit', methods=['GET','POST'])
def editItem(category_id, item_id):
    #if 'username' not in login_session:
        #return redirect('/login')
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    editedItem = session.query(Item).filter_by(id = item_id).one()
    category = session.query(Category).filter_by(id = category_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        flash('Item Successfully Edited')
        return redirect(url_for('showItems', category_id = category_id))
    else:
        return render_template('editItem.html', category_id = category_id, item_id = item_id, item = editedItem)

#Delete an item in this category
@app.route('/catalog/<int:category_id>/items/<int:item_id>/delete', methods=['GET','POST'])
def deleteItem(category_id, item_id):
    #if 'username' not in login_session:
        #return redirect('/login')
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    itemToDelete = session.query(Item).filter_by(id = item_id).one()
    category = session.query(Category).filter_by(id = category_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item Successfully Deleted')
        return redirect(url_for('showItems', category_id = category_id))
    else:
        return render_template('deleteItem.html', category_id = category_id, item_id = item_id, item = itemToDelete)

#JSON APIs to view catalog information
@app.route('/catalog/<int:category_id>/items/JSON')
def itemsJSON(category_id):
    #if 'username' not in login_session:
        #return redirect('/login')
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    #category = session.query(Category).filter_by(id = category_id).one()
    items = session.query(Item).filter_by(category_id = category_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/catalog/<int:category_id>/items/<int:item_id>/JSON')
def itemJSON(category_id, item_id):
    #if 'username' not in login_session:
        #return redirect('/login')
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    #category = session.query(Category).filter_by(id = category_id).one()
    item = session.query(Item).filter_by(id = item_id).one()
    return jsonify(Item=item.serialize)

@app.route('/catalog/JSON')
def catalogJSON():
    #if 'username' not in login_session:
        #return redirect('/login')
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    categories = session.query(Category).all()
    return jsonify(Categories= [c.serialize for c in categories])


if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)
