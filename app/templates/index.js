    function initMap() {
        var markers = {{locations|safe}};
        var centerpoint = new google.maps.LatLng(parseFloat(markers[markers.length -1][0]), parseFloat(markers[markers.length -1][1]));
        var map = new google.maps.Map(document.getElementById('map'), {
          zoom: 7,
          center: centerpoint,
          mapTypeId: google.maps.MapTypeId.ROADMAP
        });
        var infowindow = new google.maps.InfoWindow({
           maxWidth: 400
        });
        /// Add the image cluster locations
        // This is an example of the cluster information:
        // ['130',
        //  '[-12.044581875003733, -77.02696227777153]',
        //  "[['IMG_20170721_151308.jpg', -12.044618583333332, -77.02700805555557, 160, '2017-07-21 20:13:07'],
        //    ['IMG_20170721_151316.jpg', -12.044545166666667, -77.0269165, 177, '2017-07-21 20:13:16']]"]
        var cluster_markers = {{clusters|safe}}
        var cluster, i;
        for( i = 0; i < cluster_markers.length; i++ ) {
            var position = new google.maps.LatLng(parseFloat(cluster_markers[i][1][0]), parseFloat(cluster_markers[i][1][1]));
            cluster = new google.maps.Marker({
              icon: {
                  path: google.maps.SymbolPath.CIRCLE,
                  strokeWeight: 2,
                  fillOpacity: 1,
                  strokeColor: '#008000',
                  fillColor: '#FFFFFF',
                  scale: 3,
                },
                position: position,
                map: map
              });
              google.maps.event.addListener(cluster, 'click', (function(cluster, i) {
                  return function() {
                    // InfoWindow content: show all pictures in the cluster
                    var content = '';
                    for ( j = 0; j < cluster_markers[i][2].length ; j++ ) {
                      content += '<IMG BORDER="0" STYLE="width:100%" SRC="{{base_url|safe}}/images/' + cluster_markers[i][2][j][0].replace("jpg", "png") + '">'
                    };
                    infowindow.setContent(content);
                    infowindow.open(map, cluster);
                  }
              })(cluster, i));
        };
        // Add the Iridium Markers
        var marker;
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
          google.maps.event.addListener(marker, 'click', (function(marker, i) {
          return function() {
            infowindow.setContent("Date: " + markers[i][3]+ " \nAltitude: " +  markers[i][2] + "m" );
            infowindow.open(map, marker);
          }
          })(marker, i));
    };
    // Add the image locations as well
    //var image_markers = {{images|safe}}
    //var image;
    //for( i = 0; i < image_markers.length; i++ ) {
    //  if( image_markers[i][0] == 1 ) {
    //    var position = new google.maps.LatLng(parseFloat(image_markers[i][2]), parseFloat(image_markers[i][3]));
    //    image = new google.maps.Marker({
    //      icon: {
    //          path: google.maps.SymbolPath.CIRCLE,
    //          strokeWeight: 2,
    //          fillOpacity: 1,
    //          strokeColor: '#000000',
    //          fillColor: '#FFFFFF',
    //          scale: 2,
    //        },
    //        position: position,
    //        map: map
    //      });
    //      google.maps.event.addListener(image, 'click', (function(image, i) {
    //      return function() {
            //infowindow.setContent("Date: " + image_markers[i][4]+ " \nAltitude: " +  image_markers[i][3] + "m" );
    //        infowindow.setContent('<IMG BORDER="0" STYLE="width:100%" SRC="{{base_url|safe}}/images/' + image_markers[i][1].replace("jpg", "png") + '">' + image_markers[i][5]);
    //        infowindow.open(map, image);
    //      }
    //    })(image, i));
    //  };
    //};
    }
