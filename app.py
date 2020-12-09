import psycopg2  # DB connector (postgres)
import psycopg2.extras  # DB connector extras
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request  # Framework for this Web-Application
from wtforms import Form, StringField, TextAreaField, PasswordField, validators  # WTF-form for registration
from passlib.hash import sha256_crypt  # password encrypter (even in DB it will be encrypted)
from functools import wraps  # for decoration purposes (@is_logged_in)


# Initiate application
app = Flask(__name__)


# Index
@app.route('/')
def index():
    return render_template('home.html')

# About
@app.route('/about')
def about():
    return render_template('about.html')



# Articles
@app.route('/articles')
def articles():
    # Create cursor
    conn = psycopg2.connect(dbname="dahfislpfl58c2", user="tnyjbxitavzbld", password="cf1cc3c90602b68d9f8f2ec33b35bf4b2439975eec5771c2700f097c0bb5902a")
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # DictCursor is 'a must'!

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if len(articles) > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = "No Articles Found"
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()
    conn.close()


# Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    conn = psycopg2.connect(dbname="dahfislpfl58c2", user="tnyjbxitavzbld", password="cf1cc3c90602b68d9f8f2ec33b35bf4b2439975eec5771c2700f097c0bb5902a")
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # DictCursor is 'a must'!

    # Get articles
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)

    cur.close()
    conn.close()


# Random article
@app.route('/random')
def random():
    # Create cursor
    conn = psycopg2.connect(dbname="dahfislpfl58c2", user="tnyjbxitavzbld", password="cf1cc3c90602b68d9f8f2ec33b35bf4b2439975eec5771c2700f097c0bb5902a")
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # DictCursor is 'a must'!

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()
    article_ids = []
    #print(len(articles))
    #print(articles[1][0])
    for i in range(len(articles)):
        article_ids.append(articles[i][0])
    if article_ids == []:
        return render_template("home.html")
    else:
        import random
        random_id = random.choice(list(article_ids))
        int_random_id = int(random_id)

        result = cur.execute("SELECT * FROM articles WHERE id = %s", [int_random_id])

        article = cur.fetchone()

        return render_template('random.html', article=article)
        # Close connection
        cur.close()
        conn.close()
    


# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')



# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Config and initiate Postgres (MAYBE it (conn) can be placed on top as a global variable)
        conn = psycopg2.connect(dbname="dahfislpfl58c2", user="tnyjbxitavzbld", password="cf1cc3c90602b68d9f8f2ec33b35bf4b2439975eec5771c2700f097c0bb5902a")
        # Create cursor
        cur = conn.cursor()

        cur.execute("INSERT INTO users (name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to db
        conn.commit()

        # Close connection
        cur.close()
        conn.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('index'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']

        password_candidate = request.form['password']

        # Create cursor
          
        conn = psycopg2.connect(dbname="dahfislpfl58c2", user="tnyjbxitavzbld", password="cf1cc3c90602b68d9f8f2ec33b35bf4b2439975eec5771c2700f097c0bb5902a")
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) #

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", ([username]))
        result = cur.fetchall()
        result = tuple(result)
        #print(result)

        if len(result) > 0:
            # Get stored hash
            data = cur.fetchone()
            password = result[0][4]

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                #app.logger.info('PASSWORD MATCHED')
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                #app.logger.info('PASSWORD NOT MATCHED')
                error = 'Invalid password'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
            conn.close()


        else:
            # app.logger.info('NO USER')
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')


# Check if user logged in
def is_logged_in(fn):
    @wraps(fn)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return fn(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

    
# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    conn = psycopg2.connect(dbname="dahfislpfl58c2", user="tnyjbxitavzbld", password="cf1cc3c90602b68d9f8f2ec33b35bf4b2439975eec5771c2700f097c0bb5902a")
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # DictCursor is 'a must'!

    # Get articles
    result = cur.execute("SELECT * FROM articles ORDER BY id")

    articles = cur.fetchall()
    
    

    if len(articles) > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = "No Articles Found"
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()
    conn.close()



# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])


 # Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        conn = psycopg2.connect(dbname="dahfislpfl58c2", user="tnyjbxitavzbld", password="cf1cc3c90602b68d9f8f2ec33b35bf4b2439975eec5771c2700f097c0bb5902a")
        cur = conn.cursor() 

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))

        # Commit to DB
        conn.commit()

        # Close connection
        cur.close()
        conn.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create Cursor
    conn = psycopg2.connect(dbname="dahfislpfl58c2", user="tnyjbxitavzbld", password="cf1cc3c90602b68d9f8f2ec33b35bf4b2439975eec5771c2700f097c0bb5902a")
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    # Get form
    form = ArticleForm(request.form)
    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']
    
        # Create Cursor
        conn = psycopg2.connect(dbname="dahfislpfl58c2", user="tnyjbxitavzbld", password="cf1cc3c90602b68d9f8f2ec33b35bf4b2439975eec5771c2700f097c0bb5902a")
        cur = conn.cursor() 
        
        # Execute
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id = %s", (title, body, id))

        # Commit to DB
        conn.commit()

        # Close connection
        cur.close()
        conn.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create Cursor
    conn = psycopg2.connect(dbname="dahfislpfl58c2", user="tnyjbxitavzbld", password="cf1cc3c90602b68d9f8f2ec33b35bf4b2439975eec5771c2700f097c0bb5902a")
    cur = conn.cursor() 
        
    #Execute
    result = cur.execute("DELETE FROM articles WHERE id = %s", [id])
    
    # Commit to DB
    conn.commit()

    # Close connection
    cur.close()
    conn.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))



if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
