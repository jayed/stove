var current_filename = '';
var current_bg_color = '#fff';
alreadyrun = false;

var bucket_url = 'https://s3.amazonaws.com/lilscreenshare/';

// todo: put destinations in current.json
var destinations = ['racehorse', 'icecream', 'strawberry', 'pepper', 'balloon', 'banana', 'blowfish'];
var scrum_image_paths = ['./assets/img/scrum1.png', './assets/img/scrum2.png', './assets/img/scrum3.gif', './assets/img/scrum4.gif', './assets/img/scrum5.png'];



function update_stove() {
	// here, we check to see if we have a scheduled event,
	// and if not, display the current
	// we should likely pull scheduled events from current.json?
	if (!run_scheduled(11, 0, 5, get_scrum_image(), '#242424')) {  //standup time - start at 11:00 and run for 5 mins
		get_current();
	}
}

function get_current() {
	// current.json always contains our latest status, let's have a look at it
	// and if we find something new that matches our screen, update
	$.ajax({
		dataType: "json",
		url: bucket_url + 'current.json',
		cache: false,
		success: function(data) {
			if (!window.location.hash) {
				window.location.hash = destinations[0];
			}
			for (i = 0; i < destinations.length; i++) {
				var dest = destinations[i];
				if(window.location.hash === '#' + dest) {
					if (data.hasOwnProperty(dest) && data[dest].url !== current_filename) {
						current_filename = bucket_url + data[dest].url;
						$('#image-container').attr("src", current_filename);
			            if (data[dest].bg !== current_bg_color) {
                            current_bg_color = data[dest].bg;
                            $('body').css('background-color', current_bg_color);
                        }
					}
				}
			}
		}
	});
}

function run_scheduled(hour, min, display_time, file_name, bg_color) {
	// This logic helps us schedule events
	var todayHours = new Date().getHours();
	var todayMinutes = new Date().getMinutes();

	if (todayHours === hour && todayMinutes >= min && todayMinutes < min + display_time) {
		// this alreadyrun check makes sure we only sets the scrum image once per day
		if (alreadyrun == false) {
			current_filename = file_name;
			$('#image-container').attr("src", current_filename);
			current_bg_color = bg_color;
			$('body').css('background-color', current_bg_color);
		}
	    alreadyrun = true;
		return true;
	}

	alreadyrun = false;
	return false;
}

function get_scrum_image() {
	return scrum_image_paths[Math.floor(Math.random() * scrum_image_paths.length) ]
}

setInterval(update_stove, 1000)
