from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_bootstrap import Bootstrap5
from typing import List
import datetime

app = Flask(__name__)
app.secret_key = 'fdsugiowayefgoirewayfugy'
Bootstrap5(app)
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lists.db"
db.init_app(app)
COLOR_LIST = ['212529', 'ec3c36']
login_manager = LoginManager()
login_manager.init_app(app)


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id: db.Mapped[int] = db.mapped_column(primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    lists: db.Mapped[List["Lists"]] = db.relationship(back_populates="author")

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


class Lists(db.Model, UserMixin):
    __tablename__ = 'lists'
    id: db.Mapped[int] = db.mapped_column(primary_key=True)
    list_name = db.Column(db.String(80), nullable=False)
    tasks = db.Column(db.String(250))
    time = db.Column(db.String(20), nullable=False)
    author: db.Mapped["User"] = db.relationship(back_populates="lists")
    author_id: db.Mapped[int] = db.mapped_column(db.ForeignKey("user.id"))


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return db.session.execute(db.select(User).where(User.id == user_id)).scalar()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/lists', methods=['POST', 'GET'])
@login_required
def list_page():
    lists = db.session.execute(db.select(Lists).where(Lists.author == current_user)).scalars()
    list_list = []
    for list_item in lists:
        list_list.append(list_item)
    if request.method == 'POST':
        # Adding
        if request.form['new_list']:
            new_list_name = request.form['new_list']
            x = datetime.datetime.now()
            time = x.strftime("%d/%m/%Y %I:%M %p")
            new_list = Lists(
                list_name=new_list_name,
                tasks='',
                time=time,
                author=current_user,
            )
            db.session.add(new_list)
            db.session.commit()

        # Deleting
        if request.form.get('delete'):
            list_to_delete_id = int(request.form.get('delete'))
            list_to_delete = db.session.execute(db.select(Lists).where(Lists.id == list_to_delete_id)).scalar()
            db.session.delete(list_to_delete)
            db.session.commit()
        return redirect(url_for('list_page'))

    return render_template('lists.html', lists=list_list, color=COLOR_LIST)


@app.route('/task/<int:id>', methods=['POST', 'GET'])
def task(id):
    tasks = ''
    new_task = ''
    task_to_delete = None
    todo_list = db.session.execute(db.select(Lists).where(Lists.id == id)).scalar()
    print(todo_list.tasks)
    if todo_list.tasks != '':
        task_list = todo_list.tasks.split('|')
    else:
        task_list = []
    print(task_list)

    if request.method == 'POST':
        # Deleting
        if request.form.get('delete'):
            task_to_delete = int(request.form.get('delete'))
        # Adding
        if request.form.get('new_task'):
            new_task = '||' + request.form['new_task']

        # Updating Task
        if len(task_list) > 1:
            for i in range(0, len(task_list), 2):
                if i == task_to_delete:
                    continue
                if request.form.get(f'check{i}') == 'on':
                    tasks += 'checked' + '|' + task_list[i+1] + '|'
                else:
                    tasks += '' + '|' + task_list[i+1] + '|'
        else:
            if new_task:
                new_task = '|' + new_task[2:]
        tasks = tasks[:-1] + new_task

        # Updating List
        task_to_update = db.session.execute(db.select(Lists).where(Lists.id == id)).scalar()
        task_to_update.tasks = tasks
        db.session.commit()
        return redirect(url_for('task', id=id))

    return render_template('task.html', todo_list=todo_list, task_list=task_list)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user:
            if user.password == password:
                login_user(user)
                return redirect(url_for('list_page'))
            else:
                flash("Invalid Password", "error")
        else:
            flash("Invalid Email", "error")
    return render_template('login.html')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        result = db.session.execute(db.select(User).where(User.email == request.form['email'])).scalar()
        if not result:
            new_user = User(
                username=request.form['name'],
                email=request.form['email'],
                password=request.form['password'],
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return render_template('lists.html')
        else:
            flash("Email already registered, Please Login", "error")
            return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
