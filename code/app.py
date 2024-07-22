from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
#---------------------------------------

# flask db init
# flask db migrate -m "Initial Migration"
# flask db upgrade

#---------------------------------------
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bloom_data.sqlite3'

# Initialize SQLAlchemy
db = SQLAlchemy(app)
migrate = Migrate(app,db)

# app.config['SQLALCHEMY_BINDS'] = {
#     'influencer': "sqlite:///influencer.sqlite3",
#     'sponsor' : "sqlite:///sponsor.sqlite3",
# }



# Schema------------------------------
class BloomData(db.Model):
    __tablename__ = 'bloomdata'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(30), nullable=False)
    role = db.Column(db.String(30), nullable=False)

    influencer_data = db.relationship("influencerData", uselist=False, back_populates='bloomdata', cascade="all, delete-orphan")
    sponsor_data = db.relationship("sponsorData", uselist=False, back_populates='bloomdata', cascade="all, delete-orphan")

class influencerData(db.Model):
    __tablename__ = 'influencer_data'

    bloom_data_id = db.Column(db.Integer(), db.ForeignKey('bloomdata.id', ondelete="CASCADE"), primary_key=True, nullable=False, unique=True)

    name = db.Column(db.String(30), nullable=False)
    category = db.Column(db.String(30), nullable=False)
    niche = db.Column(db.String(30), nullable=False)
    reach = db.Column(db.String(30), nullable=False)


    bloomdata = db.relationship("BloomData", uselist=False, back_populates='influencer_data')

class sponsorData(db.Model):
    __tablename__ = 'sponsor_data'
    
    bloom_data_id = db.Column(db.Integer(), db.ForeignKey('bloomdata.id', ondelete="CASCADE"), primary_key=True, nullable=False, unique=True)

    company_name = db.Column(db.String(30), nullable=False)
    industry = db.Column(db.String(30), nullable=False)
    budget = db.Column(db.String(30), nullable=False)

    bloomdata = db.relationship("BloomData", uselist=False, back_populates='sponsor_data')

# User Login -------------------------------

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        email = request.form['email']
        password = request.form['password']

        # For demonstration purposes, let's just print the received data
        print("Role:", role)
        print("Email:", email)
        print("Password:", password)

        user = BloomData.query.filter_by(email=email, password=password).first()
        if user:
            if user.role == 'Influencer':
                return redirect(url_for('influencer_page'))
            elif user.role == 'Sponsor':
                return redirect(url_for('sponsor_page'))
            elif user.role == 'Admin':
                return redirect(url_for('admin_page'))
            else:
                # Handle unknown role
                return "Unknown role"
        else:
            # Handle invalid credentials
            return "Invalid credentials"
        
        # You can redirect to another page after processing the data
        return "Form submitted successfully!"  # Or redirect to another page
    return render_template("login.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method=='POST':
        role = request.form['role']
        print(f"registering as {role}") 

        e = request.form['email']
        p = request.form['password']
        entry = BloomData(email=e, password=p, role=role)
        db.session.add(entry)
        db.session.flush()  # Ensure the entry gets an ID before committing

        print(entry)

        if role=='Influencer':
            name = request.form['name']
            category = request.form['category']
            niche = request.form['niche']
            reach = request.form['reach']

            ei = request.form['email']
            pi = request.form['password']

            influencerEntry = influencerData(bloom_data_id=entry.id, name=name, category=category, niche=niche, reach=reach)
            db.session.add(influencerEntry)
            db.session.commit()

            return "influencer please login"

        elif role=='Sponsor':
            company_name = request.form['company_name']
            industry = request.form['industry']
            budget = request.form['budget']

            sponsorEntry = sponsorData(bloom_data_id=entry.id,  company_name=company_name, industry=industry, budget=budget)
            db.session.add(sponsorEntry)
            db.session.commit()

            return "sponsor please login"
        else:
            return "invalid role"
        
        

    return render_template("login.html")

@app.route("/data", methods=['GET'])
def data():
    data = BloomData.query.all()
    # print(data)
    return render_template('data.html', data=data)


@app.route('/delete/<int:id>')
def delete(id):
    # deleteingInstance = BloomData.query.filter_by(id=id)
    deleting_instance = BloomData.query.get_or_404(id)
    db.session.delete(deleting_instance)
    db.session.commit()

    return redirect(url_for('data'))

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    update_instance = BloomData.query.get_or_404(id)
    update_bloom = update_instance 
    if request.method=="GET": #name is empty as we pass the update instance instead of update_fields
        if update_instance.role=="Influencer":
            update_fields = influencerData.query.get_or_404(update_instance.id)
            return render_template('update.html', update_instance=update_fields, update_bloom=update_bloom)
        elif update_instance.role=="Sponsor":
            update_fields = sponsorData.query.get_or_404(update_instance.id)
            # print(update_fields.name)
            return render_template('update.html', update_instance=update_fields, update_bloom=update_bloom)
        else:
            return "invalid query"
    if request.method=="POST":
        e = request.form['email']
        p = request.form['password']
        r = update_instance.role
        entry = BloomData(email=e, password=p, role=r)
        db.session.add(entry)
        db.session.flush()  # Ensure the entry gets an ID before committing

        if update_instance.role=='Influencer':
            name = request.form['name']
            category = request.form['category']
            niche = request.form['niche']
            reach = request.form['reach']

            update_fields = influencerData.query.get_or_404(update_instance.id)

            update_fields.name = name
            update_fields.category = category
            update_fields.niche = niche
            update_fields.reach = reach

            influencerEntry = influencerData(bloom_data_id=entry.id, name=update_fields.name, category=update_fields.category, niche=update_fields.niche, reach=update_fields.reach)
            db.session.add(influencerEntry)
            db.session.commit()

            return "influencer please login"

        elif request.role=='Sponsor':
            company_name = request.form['company_name']
            industry = request.form['industry']
            budget = request.form['budget']

            sponsorEntry = sponsorData(bloom_data_id=entry.id,  company_name=company_name, industry=industry, budget=budget)
            db.session.add(sponsorEntry)
            db.session.commit()

            return "sponsor please login"
        else:
            return "invalid role"

    return render_template('update.html', update_instance=update_instance, update_bloom=update_bloom)

# ----------------------------------------
@app.route('/influencer')
def influencer_page(): 
    return "Welcome Influencer!"
@app.route('/influencer-registration') 
def influencer_reg():
    return render_template('influencer-reg.html')

@app.route('/sponsor')
def sponsor_page():
    return "Welcome Sponsor!"
@app.route('/sponsor-registration')
def sponsor_reg():
    return render_template('sponsor-reg.html')

@app.route('/admin')
def admin_page():
    return "Welcome Admin!"

# Home Page -------------------------------
@app.route("/")
def home():
    return render_template('index.html')



if __name__ == "__main__":
    app.run(debug=True, port=5050)