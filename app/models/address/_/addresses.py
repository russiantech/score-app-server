from flask_jwt_extended import current_user
from sqlalchemy import func
from web.extensions import db

class Country(db.Model):
    __tablename__ = 'countries'
    id = db.Column(db.Integer, primary_key=True)
    geoname_id = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(140), nullable=False, unique=True)
    languages = db.Column(db.String(255))
    iso_numeric = db.Column(db.String(10), unique=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    currency = db.Column(db.String(50))
    currency_symbol = db.Column(db.String(10), nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)
    flag_url = db.Column(db.String(255), nullable=True)
    states = db.relationship('State', backref='country', lazy=True)
    created_at = db.Column(db.DateTime, index=True, nullable=False, default=func.now())

    def get_summary(self, include_states=False):
        # Determine if the user has selected this country before
        is_selected = False
        if current_user and current_user.addresses:
            for address in current_user.addresses:
                if address.city and address.city.state and address.city.state.country.id == self.id:
                    is_selected = True
                    break

        data = {
            'id': self.id,
            'name': self.name,
            'is_selected': is_selected,
            'created_at': self.created_at
        }
        
        if include_states:
            data['states'] = [state.get_summary() for state in self.states]
        
        return data

class State(db.Model):
    __tablename__ = 'states'

    id = db.Column(db.Integer, primary_key=True)
    geoname_id = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(140), nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    cities = db.relationship('City', backref='state', lazy=True)

    created_at = db.Column(db.DateTime, index=True, nullable=False, default=func.now())

    def get_summary(self, include_cities=False):
        data = {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at
        }
        if include_cities:
            data['cities'] = [city.get_summary() for city in self.cities]
        return data

class City(db.Model):
    __tablename__ = 'cities'

    id = db.Column(db.Integer, primary_key=True)
    geoname_id = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(140), nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)

    created_at = db.Column(db.DateTime, index=True, nullable=False, default=func.now())

    def get_summary(self):
        return {
            'id': self.id,
            'name': self.name,
            'geoname_id': self.geoname_id,
            'state_id': self.state_id,
            'created_at': self.created_at
        }

class Address(db.Model):
    __tablename__ = 'addresses'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(140), nullable=False)
    last_name = db.Column(db.String(140))
    street_address = db.Column(db.String(140), nullable=False)
    zip_code = db.Column(db.String(20))
    house = db.Column(db.String(20))
    floor = db.Column(db.String(20))
    customer_email = db.Column(db.String(140), nullable=True)
    phone_number = db.Column(db.String(140), nullable=True)
    adrs_type = db.Column(db.Enum('user', 'store', name='address_type'), nullable=False, default='user')
    is_primary = db.Column(db.Boolean(), nullable=False, default=False)
    is_deleted = db.Column(db.Boolean(), nullable=False, default=False)
    created_at = db.Column(db.DateTime, index=True, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    pages = db.relationship('Page', back_populates='addresses', uselist=False)
    # stores = db.relationship('Store', back_populates='addresses') # removed uselist entirely if a 1 address allows multiple stores 
    stores = db.relationship('Store', back_populates='addresses', uselist=False)
    city = db.relationship('City', backref='addresses')
    users = db.relationship('User', back_populates='addresses')
    orders = db.relationship('Order', back_populates='addresses', cascade='all, delete-orphan')

    def get_summary(self, **kwargs):
        """
        Safe serialization with null checks and unlimited args support
        Usage examples:
        - address.get_summary()  # Basic info
        - address.get_summary(include_city=True, include_user=True, include_store=True)
        """
        include_city = kwargs.get('include_city', True)
        include_user = kwargs.get('include_user', False)
        include_state = kwargs.get('include_state', False)
        include_country = kwargs.get('include_country', False)
        include_store = kwargs.get('include_store', False)  # New parameter
        
        data = {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'street_address': self.street_address,
            'zip_code': self.zip_code,
            'phone_number': self.phone_number,
            'is_primary': self.is_primary,
            'type': self.adrs_type,
            'is_store': (self.stores is not None),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        # Handle city with null check
        if include_city and self.city:
            city_data = {
                'id': self.city.id,
                'name': self.city.name
            }
            
            # Include state if requested
            if include_state and self.city.state:
                state_data = {
                    'id': self.city.state.id,
                    'name': self.city.state.name
                }
                
                # Include country if requested
                if include_country and self.city.state.country:
                    state_data['country'] = {
                        'id': self.city.state.country.id,
                        'name': self.city.state.country.name,
                        'code': self.city.state.country.code
                    }
                
                city_data['state'] = state_data
            
            data['city'] = city_data
        elif include_city:
            data['city'] = None

        # Handle user relationship
        if include_user:
            data['user'] = {
                'id': self.user_id,
                'username': self.users.username if self.users else None
            }
            
        # Handle store information if requested and exists
        if include_store and self.stores:
            data['stores'] = {
                'id': self.stores.id,
                'name': self.stores.name,
                'phone': self.stores.phone,
                'email': self.stores.email,
                'hours': self.stores.hours,
            }

        return data

class ContactInfo(db.Model):
    __tablename__ = 'contact_infos'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    first_name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    preferred_contact = db.Column(db.Enum('email', 'phone', 'both'))
    
    product = db.relationship('Product', back_populates='contact_info')

class Location(db.Model):
    __tablename__ = 'locations'
    __table_args__ = (
        db.Index('ix_location_coords', 'latitude', 'longitude'),  # Composite index
    )
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    latitude = db.Column(db.Numeric(9,6), comment='Range: -90.000000 to 90.000000', nullable=True)
    longitude = db.Column(db.Numeric(9,6), comment='Range: -180.000000 to 180.000000', nullable=True)
    address = db.Column(db.Text, nullable=True)
    zoom_level = db.Column(db.Integer, default=12)
    product = db.relationship('Product', back_populates='location')
    
    __table_args__ = (
        db.CheckConstraint('latitude BETWEEN -90 AND 90', name='chk_latitude'),
        db.CheckConstraint('longitude BETWEEN -180 AND 180', name='chk_longitude'),
    )
