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

# Load the client secrets file I downloaded from Google OAuth
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Udacity Item Catalog"

#Connect to Database and create database session
#Note that we have to bind the session separately in every method
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

#Handling the response from Google Sign-in
#NOTE: the id returned is referred to as gplus_id for legacy reasons,
# even though the Google Plus API is no longer used
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # check if a user exists, if not add user to User table
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    # send a login in message while redirecting
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# disconnect a user that logs out
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# oauth login
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

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
    # users need to be logged in to do CUD operations
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        DBSession = sessionmaker(bind=engine)
        session = DBSession()
        newCategory = Category(name = request.form['name'], user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newCategory.html')

#Edit a category
@app.route('/catalog/<int:category_id>/edit/', methods = ['GET', 'POST'])
def editCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    editedCategory = session.query(Category).filter_by(id = category_id).one()
    # make sure users can only edit their own categories/items
    if editedCategory.user_id != login_session['user_id']:
        return "You are not authorized to alter this category."
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
    if 'username' not in login_session:
        return redirect('/login')
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    categoryToDelete = session.query(Category).filter_by(id = category_id).one()
    if categoryToDelete.user_id != login_session['user_id']:
        return "You are not authorized to alter this category."
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
#This is not used in current build, as there is no HTML template yet
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
    if 'username' not in login_session:
        return redirect('/login')
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).filter_by(id = category_id).one()
    if request.method == 'POST':
        newItem = Item(name = request.form['name'], description = request.form['description'], category_id = category_id, user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('New Item %s Successfully Created' % (newItem.name))
        return redirect(url_for('showItems', category_id = category_id))
    else:
        return render_template('newItem.html', category_id = category_id)

#Edit an item in this category
@app.route('/catalog/<int:category_id>/items/<int:item_id>/edit', methods=['GET','POST'])
def editItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    editedItem = session.query(Item).filter_by(id = item_id).one()
    category = session.query(Category).filter_by(id = category_id).one()
    if editedItem.user_id != login_session['user_id']:
        return "You are not authorized to alter this item."
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
    if 'username' not in login_session:
        return redirect('/login')
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    itemToDelete = session.query(Item).filter_by(id = item_id).one()
    category = session.query(Category).filter_by(id = category_id).one()
    if itemToDelete.user_id != login_session['user_id']:
        return "You are not authorized to alter this category."
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


#Methods to handle user creation and validation
#NOTE: We're intentionally ignoring the 'picture' field
def createUser(login_session):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    newUser = User(name = login_session['username'], email =
        login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email =
        login_session['email']).one()
    return user.id

def getUserInfor(user_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    user = session.query(User).filter_by(id = user_id).one()
    return user

def getUserID(email):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    try:
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None


if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)
