<html>
<head>
<meta name="viewport" content="initial-scale=1.0, user-scalable=no" />
<script type="text/javascript" src="http://maps.google.com/maps/api/js?sensor=false"></script>
<script type="text/javascript">
var qsParm = new Array();

function qs() {
	var query = window.location.search.substring(1);
	var parms = query.split('&');
	for (var i=0; i<parms.length; i++) {
		var pos = parms[i].indexOf('=');
		if (pos > 0) {
			var key = parms[i].substring(0,pos);
			var val = parms[i].substring(pos+1);
			qsParm[key] = val;
		}
	}
}

function updatePosition(id)
{
	var lat = document.getElementById("latitude").innerHTML
	var lng = document.getElementById("longtitude").innerHTML

	if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
  		xmlhttp=new XMLHttpRequest();
  	} else {// code for IE6, IE5
  		xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  	}
	xmlhttp.onreadystatechange=function() {
  		if (xmlhttp.readyState==4 && xmlhttp.status==200) {
    			document.getElementById("txtHint").innerHTML=xmlhttp.responseText;
    		}
  	}
	xmlhttp.open("GET","updatePosition.php?id="+id+"&lat="+lat+"&lng="+lng,true);
	xmlhttp.send();
	window.alert("Save Complete")

}


var geocoder = new google.maps.Geocoder();

function geocodePosition(pos) {
  geocoder.geocode({
    latLng: pos
  }, function(responses) {document.getElementById("txtHint").innerHTML
    if (responses && responses.length > 0) {
      updateMarkerAddress(responses[0].formatted_address);
    } else {
      updateMarkerAddress('Cannot determine address at this location.');
    }
  });
}

function updateMarkerStatus(str) {
  document.getElementById('markerStatus').innerHTML = str;
}

function updateMarkerPosition(latLng) {
  document.getElementById('latitude').innerHTML = latLng.lat()
  document.getElementById('longtitude').innerHTML = latLng.lng()
}

function updateMarkerAddress(str) {
  document.getElementById('address').innerHTML = str;
}

function initialize() {
  qsParm['lat'] = null;
  qsParm['lng'] = null;
  qs();
  var latLng = new google.maps.LatLng(qsParm['lat'], qsParm['lng']);	
  //var latLng = new google.maps.LatLng(-34.397, 150.644);
  var map = new google.maps.Map(document.getElementById('mapCanvas'), {
    zoom: 17,
    center: latLng,
    mapTypeId: google.maps.MapTypeId.ROADMAP
  });
  var marker = new google.maps.Marker({
    position: latLng,
    title: 'Point A',
    map: map,
    draggable: true
  });
  
  // Update current position info.
  updateMarkerPosition(latLng);
  geocodePosition(latLng);
  
  // Add dragging event listeners.
  google.maps.event.addListener(marker, 'dragstart', function() {
    updateMarkerAddress('Dragging...');
  });
  
  google.maps.event.addListener(marker, 'drag', function() {
    updateMarkerStatus('Dragging...');
    updateMarkerPosition(marker.getPosition());
  });
  
  google.maps.event.addListener(marker, 'dragend', function() {
    updateMarkerStatus('Drag ended');
    geocodePosition(marker.getPosition());
  });
}

// Onload handler to fire off the app.
google.maps.event.addDomListener(window, 'load', initialize);
</script>
<style type="text/css">
  #mapCanvas{ width:100%; height: 400px }
</style>
</head>

<?php
	session_start();
	$_SESSION['uid'] = $_GET['uid'];
	$_SESSION['pwd'] = $_GET['pwd'];
	$_SESSION['dbname'] = $_GET['dbname'];
	$_SESSION['host'] = $_GET['host'];
?>
<body>
  <table width="100%">
    	<tr>
		<td height="400px"><div id="mapCanvas"></div></td>
	</tr>
    	<tr>
		<td>
  <div id="infoPanel">
    <b>Marker status:</b>
    <div id="markerStatus"><i>Click and drag the marker.</i></div>
    <b>Current position:</b>
    <div id="latitude"></div><div id="longtitude"></div>
    <b>Closest matching address:</b>
    <div id="address"></div>
    <div id="txtHint"></div>
  </div>
<form name='myForm'>	
	<?php echo "<input type='button' onclick='updatePosition(".$_GET['id'] .")' value='Update Position' />" ?>
	
</form>
</td>
	</tr>
  </table>
  
</body>
</html>
