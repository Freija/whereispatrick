(function () {
    'use strict';

    function initMap() {
        var markers = {{locations|safe}};
        var centerpoint = new google.maps.LatLng(parseFloat(markers[markers.length -1][0]), parseFloat(markers[markers.length -1][1]));
        var map = new google.maps.Map(document.getElementById('map'), {
          zoom: 7,
          center: centerpoint,
          mapTypeId: google.maps.MapTypeId.ROADMAP
        });
        var infowindow = new google.maps.InfoWindow();
        // Add the Iridium Markers
        var marker, i;
        for( i = 0; i < markers.length; i++ ) {
          var position = new google.maps.LatLng(parseFloat(markers[i][0]), parseFloat(markers[i][1]));
          if( i< markers.length-1 ) {
            marker = new google.maps.Marker({
              icon: {
                path: google.maps.SymbolPath.CIRCLE,
                strokeWeight: 2,
                fillOpacity: 1,
                strokeColor: '#FF0000',
                fillColor: '#FFFFFF',
                scale: 5,
              },
              position: position,
              map: map
            });
          }
          else {
            marker = new google.maps.Marker({
              position: position,
              map: map
            });
          }
          //console.log(position);
          google.maps.event.addListener(marker, 'click', (function(marker, i) {
          return function() {
            infowindow.setContent("Date: " + markers[i][3]+ " \nAltitude: " +  markers[i][2] + "m" );
            infowindow.open(map, marker);
          }
          })(marker, i));
    };
    // Add the image locations as well
    var image_markers = {{images|safe}}
    var image;
    for( i = 0; i < image_markers.length; i++ ) {
      var position = new google.maps.LatLng(parseFloat(image_markers[i][1]), parseFloat(image_markers[i][2]));
      image = new google.maps.Marker({
        icon: {
            path: google.maps.SymbolPath.CIRCLE,
            strokeWeight: 2,
            fillOpacity: 1,
            strokeColor: '#000000',
            fillColor: '#FFFFFF',
            scale: 2,
          },
          position: position,
          map: map
        });
        google.maps.event.addListener(image, 'click', (function(image, i) {
        return function() {
          //infowindow.setContent("Date: " + image_markers[i][4]+ " \nAltitude: " +  image_markers[i][3] + "m" );
          infowindow.setContent('<IMG BORDER="0" STYLE="width:100%" SRC="{{base_url|safe}}/images/' + image_markers[i][0] + '">' + image_markers[i][4]);
          infowindow.open(map, image);
        }
      })(image, i));
      };
    }

}());
