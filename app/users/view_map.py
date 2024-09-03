from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint
from settings import Config
import geocoder
from geopy.distance import geodesic
import folium

view_map_bp = Blueprint('view_map_bp', __name__, template_folder='templates/users', static_folder='static')

g = geocoder.ipinfo('me')#access ip address
data = Config.opportunities#data for opportunities

access_token=Config.mapbox

#get information from models of company and advertisements especially the name, seeking for and latitude


@view_map_bp.route('/view_map')
def View_map():
	try:
		my_map = folium.Map(location=[g.lat, g.lng], zoom_start=10, tiles='CartoDB positron')#base map
		#add google maps as a layer
		# Choose a Mapbox style (e.g., 'streets', 'satellite', 'outdoors')
		folium.TileLayer(tiles='https://api.mapbox.com/styles/v1/mapbox/satellite-v9?access_token={token}',
                url_fmt='//{s}.tiles.mapbox.com/{z}/{x}/{y}@2x',
                attr='Mapbox',
                tile_size=256,
                style_url='satellite-v9',  # Corrected style URL
                token=access_token).add_to(my_map)
		#folium.TileLayer(tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors').add_to(my_map)
		#folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', attr='GoogleMaps').add_to(my_map)
		
		# Get company data from model (replace with your actual logic)
		  # Placeholder, replace with actual data retrieval

		# Add a marker for your current position
		folium.Marker(
			location=[g.lat, g.lng],
			popup="Your here",
			draggable=False,
			tooltip="you are here",
			icon=folium.Icon(color="blue", size=(50, 50)) 
			).add_to(my_map)


        # Add markers for company locations 
		company_data = data.show()
		for company in company_data:
			hire_pin = folium.features.CustomIcon('static/images/view_map_pin.png', icon_size=(17,17))
			distance_in_km = geodesic((g.lat,g.lng), (company[19],company[20])).km.__ceil__() #.__ceil__() is a function for rounding up
			distance_in_m = geodesic((g.lat,g.lng), (company[19],company[20])).m.__ceil__()
			folium.Marker(
				location=[company[19], company[20]], 
				draggable=True,
				tooltip=f"{company[1]} \n looking for {company[6]}",
				popup=f"{company[1]} \n looking for {company[6]} \n <a href='mailto:{company[2]}'>{company[2]}</a> \n <a href='tel:{company[3]}'>{company[3]}</a>. <strong>{distance_in_km}km</strong> or <strong>{distance_in_m}m</strong> far from you.",
				icon=hire_pin
				).add_to(my_map)
								
																		
		# Render the map
		map_html = my_map.get_root().render()
	except ValueError:
	   flash('Hire maps is not responding, check your connection!')
	   return redirect(url_for('welcome_bp.Welcome'))
		
	if g.status == 'OK':
		flash('Hire maps is not responding, check your connection!')
		return render_template('view_map.html', map_html=map_html)
	else:
	   flash('Check your internet connection!!')
	   return redirect(url_for('welcome_bp.Welcome'))
