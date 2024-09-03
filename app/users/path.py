from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint
from settings import Config
import geocoder
from geopy.distance import geodesic
import folium

path_bp = Blueprint('path_bp', __name__, template_folder='templates/users', static_folder='static')
 
g = geocoder.ipinfo('me')#access ip address
access_token=Config.mapbox

@path_bp.route('/path_bp', methods=['POST'])
def Path():
	if request.method == 'POST':
		row_name = request.form.get('company_popup')
		row_lat = request.form.get('Lat') # Get the lat from the form data
		row_lng = request.form.get('Long')  # Get the lng from the form data
		row_call = request.form.get('Call')  # Get the call from the form data
		row_email = request.form.get('Email')  # Get the email from the form data
		try:
			my_map = folium.Map(location=[g.lat, g.lng], zoom_start=10)#basemap
		
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
			
			# Add a marker for your current position
			folium.Marker(
				location=[g.lat, g.lng],
				popup="Your location",
				draggable=False,
				tooltip="You are here",
				icon=folium.Icon(color="blue") 
				).add_to(my_map)
					
				#for company
			hire_pin = folium.features.CustomIcon('static/images/view_map_pin.png', icon_size=(17,17))
			distance_in_km = geodesic((g.lat,g.lng), (row_lat,row_lng)).km.__ceil__() #.__ceil__() is a function for rounding up
			distance_in_m = geodesic((g.lat,g.lng), (row_lat,row_lng)).m.__ceil__()

			folium.Marker(
				location=[row_lat, row_lng],
				popup=f"<strong>{row_name}</strong> is <strong>{distance_in_km}km</strong> or <strong>{distance_in_m}m</strong> from you. \n <a href='mailto:{row_email}'>{row_email}</a> \n <a href='tel:{row_call}'>{row_call}</a>", 
                icon=hire_pin,
				draggable=True,
				tooltip=f"<strong>{row_name}</strong>"
				).add_to(my_map)
				
			folium.PolyLine(
				locations=[[g.lat, g.lng],
				[row_lat, row_lng]], color='black'
				).add_to(my_map)
			
			# Render the map
			map_html = my_map.get_root().render()
		except ValueError:
			flash('Hire maps is not responding, check your connection!')
			return redirect(url_for('view_map_bp.View_map'))
			
		if g.status == 'OK':
			flash("Explore all the opportunities around you")
			return render_template('view_map.html', map_html=map_html)
		else:
			flash('Hire maps is not responding, check your connection!')
			return redirect(url_for('welcome_bp.Welcome'))	    
	else:
		return redirect(url_for('welcome_bp.Welcome'))	        
  