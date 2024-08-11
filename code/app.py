from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session
from sqlalchemy.orm import Session

from werkzeug.security import check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
#---------------------------------------

# flask db init
# flask db migrate -m "Initial Migration"
# flask db upgrade

#---------------------------------------
app = Flask(__name__)
app.secret_key = 'TOKO_YANI'

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
    flagged = db.Column(db.Boolean, default=False)


    bloomdata = db.relationship("BloomData", uselist=False, back_populates='influencer_data')

class sponsorData(db.Model):
    __tablename__ = 'sponsor_data'
    
    bloom_data_id = db.Column(db.Integer(), db.ForeignKey('bloomdata.id', ondelete="CASCADE"), primary_key=True, nullable=False, unique=True)

    company_name = db.Column(db.String(30), nullable=False)
    industry = db.Column(db.String(30), nullable=False)
    budget = db.Column(db.String(30), nullable=False)
    flagged = db.Column(db.Boolean, default=False)

    bloomdata = db.relationship("BloomData", uselist=False, back_populates='sponsor_data')

class campaign(db.Model):
    __tablename__ = 'campaigns'
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    niche = db.Column(db.String(50), nullable=False)
    deadline = db.Column(db.Date, nullable=False)

class CampaignRequest(db.Model):
    __tablename__ = 'campaign_requests'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer_data.bloom_data_id'), nullable=False)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor_data.bloom_data_id'), nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Added status field
    
    campaign = db.relationship('campaign', backref=db.backref('requests', lazy=True))
    influencer = db.relationship('influencerData', backref=db.backref('requests', lazy=True))
    sponsor = db.relationship('sponsorData', backref=db.backref('requests', lazy=True))
    
    __table_args__ = (
        db.UniqueConstraint('campaign_id', 'influencer_id', name='unique_campaign_influencer'),
    )
class AdRequest(db.Model):
    __tablename__ = 'ad_requests'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer_data.bloom_data_id'), nullable=False)
    messages = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, nullable=False)
    payment_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Could be Pending, Accepted, Rejected

    campaign = db.relationship('campaign', backref=db.backref('ad_requests', lazy=True))
    influencer = db.relationship('influencerData', backref=db.backref('ad_requests', lazy=True))

@app.route('/open_ad_request', methods=['GET'])
def open_ad_request():
    user_id = session.get('user_id')
    if user_id:
        user = BloomData.query.get(user_id)
        sdata = sponsorData.query.get(user_id)
        campaigns = campaign.query.all()  # Adjust this to get the list of campaigns
        influencers = influencerData.query.all()  # Adjust this to get the list of influencers
        return render_template('sponsor_add_ad.html', user=user, sdata=sdata, campaigns=campaigns, influencers=influencers)

@app.route('/create_ad_request', methods=['POST'])
def create_ad_request():
    campaign_id = request.form.get('campaign_id')
    influencer_id = request.form.get('influencer_id')  # This should be the bloom_data_id of the influencer
    messages = request.form.get('messages')
    requirements = request.form.get('requirements')
    payment_amount = request.form.get('payment_amount')

    # Print the form data to the terminal
    print(f"Campaign ID: {campaign_id}")
    print(f"Influencer ID: {influencer_id}")
    print(f"Messages: {messages}")
    print(f"Requirements: {requirements}")
    print(f"Payment Amount: {payment_amount}")
    
    # Process the form data (e.g., save to the database)
    new_ad_request = AdRequest(
        campaign_id=campaign_id,
        influencer_id=influencer_id,
        messages=messages,
        requirements=requirements,
        payment_amount=payment_amount,
        status='Pending'
    )
    db.session.add(new_ad_request)
    db.session.commit()

    return redirect(url_for('open_ad_request'))

@app.route('/ad_request_form/<int:campaign_id>/<int:influencer_id>', methods=['GET'])
def ad_request_form(campaign_id, influencer_id):
    # Fetch the campaign details
    campaign = campaign.query.get(campaign_id)
    if not campaign:
        return "Campaign not found.", 404

    # Pass the campaign and influencer details to the template
    return render_template('ad_request_form.html', 
                           campaign=campaign, 
                           influencer_id=influencer_id)


@app.route('/update_ad_request/<int:ad_request_id>', methods=['POST'])
def update_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    
    # Get form values
    ad_request.messages = request.form.get('messages')
    ad_request.requirements = request.form.get('requirements')

    payment_amount_str = request.form.get('payment_amount')
    try:
        ad_request.payment_amount = float(payment_amount_str) if payment_amount_str else ad_request.payment_amount
    except ValueError:
        return "Invalid payment amount.", 400

    ad_request.status = request.form.get('status', ad_request.status)  # Default to current status if not provided

    db.session.commit()

    return redirect(url_for('view_ad_requests'))
@app.route('/view_ad_request', methods=['GET'])
def view_ad_request():
    user_id = session.get('user_id')
    if user_id:
        # Retrieve the sponsor data
        sdata = sponsorData.query.get(user_id)
        
        # Retrieve all campaign requests related to the sponsor
        campaign_requests = CampaignRequest.query.filter_by(sponsor_id=user_id).all()
        campaign_ids = [cr.campaign_id for cr in campaign_requests]
        
        # Retrieve all ad requests for the campaigns belonging to this sponsor
        ad_requests = AdRequest.query.filter(AdRequest.campaign_id.in_(campaign_ids)).all()
        
        return render_template('sponsor_add_existing.html', sdata=sdata, ad_requests=ad_requests)
    else:
        return redirect(url_for('login'))  # Redirect to login if not authenticated

@app.route('/submit_campaign', methods=['POST'])
def submit_campaign():
    title = request.form['title']
    description = request.form['description']
    niche = request.form['niche']
    deadline_str = request.form['deadline']
    

    # Convert the string to a Python date object
    deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()

    new_campaign = campaign(title=title, description=description, niche=niche, deadline=deadline)
    db.session.add(new_campaign)
    db.session.commit()

    return redirect(url_for('add_campaigns'))

@app.route('/add-campaign', methods=['POST'])
def add_campaign():
    title = request.form['title']
    description = request.form['description']
    niche = request.form['niche']
    deadline = request.form['deadline']

    # Convert the deadline to a datetime object
    deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()

    # Create a new Campaign instance
    new_campaign = campaign(title=title, description=description, niche=niche, deadline=deadline_date)

    # Add the new campaign to the database
    db.session.add(new_campaign)
    db.session.commit()

    return redirect(url_for('add_campaigns'))  # Redirect to a relevant page after saving the data
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
        print(user)

        # Check if the user is an admin
        if role == "Admin":
            #hardcoded
            if email == 'roshanekka@icloud.com' and password == 'qwerty123':
                return redirect(url_for('admin_page'))
            else:
                return "Invalid admin credentials"
            
         # Check if the user is an Influencer or Sponsor
        user = BloomData.query.filter_by(email=email, password=password, role=role).first()
        if user:
            session['user_id'] = user.id
            session['role'] = role

            if role == 'Influencer':
                # idata = influencerData.query.get(user.id)
                idata = db.session.get(influencerData, user.id)
                # return render_template('influencer.html', user=user, idata=idata)
                return redirect(url_for('influencer_page', user_id=user.id, idata=idata))
                return redirect(url_for('influencer_page'))
            elif role == 'Sponsor':
                # sdata = sponsorData.query.get(user.id)
                sdata = db.session.get(sponsorData, user.id)
                return redirect(url_for('sponsor_page', user_id=user.id, sdata=sdata))
                return redirect(url_for('sponsor_page'))
        else:
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
@app.route('/find_campaigns', methods=['GET', 'POST'])
def find_campaigns():
    title_query = request.form.get('title', '')
    niche_query = request.form.get('niche', '')
    deadline_query = request.form.get('deadline', '')

    # Build the query
    query = campaign.query

    if title_query:
        query = query.filter(campaign.title.ilike(f'%{title_query}%'))
    if niche_query:
        query = query.filter(campaign.niche.ilike(f'%{niche_query}%'))
    if deadline_query:
        try:
            deadline_date = datetime.strptime(deadline_query, '%Y-%m-%d').date()
            query = query.filter(campaign.deadline == deadline_date)
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD.", 400

    campaigns = query.all()

    # Get user id from session
    user_id = session.get('user_id')
    
    if user_id:
        idata = influencerData.query.get(user_id)
        return render_template('campaign_find.html', campaigns=campaigns, idata=idata)
    else:
        return redirect(url_for('login'))  # Redirect to login if not authenticated

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
    user_id = session.get('user_id')
    if user_id:
        user = BloomData.query.get(user_id)
        idata = influencerData.query.get(user_id)
        
        # Fetch all campaign requests associated with this influencer
        requests = CampaignRequest.query.filter_by(influencer_id=user_id).all()
        
        return render_template('influencer_profile.html', user=user, idata=idata, requests=requests)
    else:
        return redirect(url_for('login'))  # Redirect to 

@app.route('/sponsor_campaign')
def add_campaigns(): 
    user_id = session.get('user_id')
    campaigns = campaign.query.all()
    if user_id:
        user = BloomData.query.get(user_id)
        sdata = sponsorData.query.get(user_id)
        return render_template('add_campaigns.html', user=user, sdata=sdata, campaigns=campaigns)

@app.route('/influencer-registration') 
def influencer_reg():
    return render_template('influencer-reg.html')

@app.route('/find_sponsors', methods=['GET', 'POST'])
def find_sponsors_admin():
    sponsors = db.session.query(sponsorData, BloomData.email).join(BloomData, sponsorData.bloom_data_id == BloomData.id).all()
    return render_template('admin_find_sponsor.html', sponsors=sponsors)

@app.route('/find_influencers', methods=['GET', 'POST'])
def find_influencers_admin():
    influencers = db.session.query(influencerData, BloomData.email).join(BloomData, influencerData.bloom_data_id == BloomData.id).all()
    return render_template('admin_find_influencer.html', influencers=influencers)

@app.route('/toggle_flag_sponsor/<int:sponsor_id>', methods=['POST'])
def toggle_flag_sponsor(sponsor_id):
    sponsor = sponsorData.query.get_or_404(sponsor_id)
    sponsor.flagged = not sponsor.flagged  # Toggle the flag status
    db.session.commit()
    return redirect(url_for('find_sponsors_admin'))

@app.route('/toggle_flag_influencer/<int:influencer_id>', methods=['POST'])
def toggle_flag_influencer(influencer_id):
    influencer = influencerData.query.get_or_404(influencer_id)
    influencer.flagged = not influencer.flagged  # Toggle the flag status
    db.session.commit()
    return redirect(url_for('find_influencers_admin'))

@app.route('/sponsor_find_influencers', methods=['GET', 'POST'])
def sponsor_find_influencers():
    user_id = session.get('user_id')
    niche_query = request.form.get('niche')

    # Fetch the campaigns from the database
    campaigns = campaign.query.all()

    if user_id:
        influencers = influencerData.query.all()  # Assuming `influencerData` is your model for influencers
        user = BloomData.query.get(user_id)
        sdata = sponsorData.query.get(user_id)

        if niche_query:
            influencers = influencerData.query.filter(influencerData.niche.like(f'%{niche_query}%')).all()
        else:
            influencers = influencerData.query.all()  # If no search, return all influencers
        
        # Pass the campaigns to the template
        return render_template('sponsor_find.html', user=user, sdata=sdata, influencers=influencers, niche_query=niche_query, campaigns=campaigns) 

@app.route('/decline_request/<int:request_id>', methods=['POST'])
def decline_request(request_id):
    request_to_decline = CampaignRequest.query.get_or_404(request_id)
    request_to_decline.status = 'Declined'
    db.session.commit()
    
    return redirect(url_for('influencer_page'))

@app.route('/accept_request/<int:request_id>', methods=['POST'])
def accept_request(request_id):
    request_to_accept = CampaignRequest.query.get_or_404(request_id)
    request_to_accept.status = 'Accepted'
    db.session.commit()
    
    return redirect(url_for('influencer_page'))

@app.route('/sponsor')
def sponsor_page():
    user_id = session.get('user_id')
    if user_id:
        user = BloomData.query.get(user_id)
        sdata = sponsorData.query.get(user_id)
        return render_template('sponsor_profile.html', user=user, sdata=sdata)

@app.route('/sponsor-registration')
def sponsor_reg():
    return render_template('sponsor-reg.html')
@app.route("/logout")
def logout():
    session.clear()  # Clear all data from the session
    return redirect(url_for('login'))  # Redirect to the login page or homepage
@app.route('/admin')
def admin_page():
    # Fetch all BloomData (users)
    bloom_data = BloomData.query.all()
    
    # Initialize lists to hold influencer and sponsor data
    influencers = []
    sponsors = []
    
    # Fetch data for influencers and sponsors
    for entry in bloom_data:
        if entry.role == 'Influencer':
            influencer = influencerData.query.get(entry.id)
            influencers.append({
                'email': entry.email,
                'name': influencer.name,
                'category': influencer.category,
                'niche': influencer.niche,
                'reach': influencer.reach
            })
        elif entry.role == 'Sponsor':
            sponsor = sponsorData.query.get(entry.id)
            sponsors.append({
                'email': entry.email,
                'company_name': sponsor.company_name,
                'industry': sponsor.industry,
                'budget': sponsor.budget
            })
    
    # Fetch all campaigns
    campaigns = campaign.query.all()
    
    # Fetch all campaign requests
    requests = CampaignRequest.query.all()
    
    return render_template('admin_profile.html', 
                           influencers=influencers, 
                           sponsors=sponsors, 
                           campaigns=campaigns, 
                           requests=requests)

@app.route('/edit_campaign/<int:campaign_id>', methods=['POST'])
def edit_campaign(campaign_id):
    campaign_to_edit = campaign.query.get(campaign_id)
    
    campaign_to_edit.title = request.form['title']
    campaign_to_edit.description = request.form['description']
    campaign_to_edit.niche = request.form['niche']
    campaign_to_edit.deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d').date()

    db.session.commit()
    
    return redirect(url_for('add_campaigns'))

@app.route('/delete_campaign/<int:campaign_id>', methods=['POST'])
def delete_campaign(campaign_id):
    # Get the campaign to delete
    campaign_to_delete = campaign.query.get_or_404(campaign_id)

    # Check if there are any requests associated with this campaign
    requests_to_delete = CampaignRequest.query.filter_by(campaign_id=campaign_id).all()
    for request in requests_to_delete:
        db.session.delete(request)

    # Delete the campaign itself
    db.session.delete(campaign_to_delete)
    db.session.commit()

    return redirect(url_for('add_campaigns'))

@app.route('/request_influencer/<int:influencer_id>', methods=['POST'])
def request_influencer(influencer_id):
    campaign_id = request.form.get('campaign_id')
    sponsor_id = session.get('user_id')

    # Check if a request already exists for this campaign and influencer
    existing_request = CampaignRequest.query.filter_by(campaign_id=campaign_id, influencer_id=influencer_id).first()

    if existing_request:
        return "Request already exists for this campaign and influencer.", 400

    # Create a new campaign request
    new_request = CampaignRequest(campaign_id=campaign_id, influencer_id=influencer_id, sponsor_id=sponsor_id)
    db.session.add(new_request)
    db.session.commit()

    return redirect(url_for('sponsor_find_influencers'))
# Home Page -------------------------------
@app.route("/")
def home():
    return render_template('index.html')



if __name__ == "__main__":
    app.run(debug=True, port=5050)