var current_filename = '';
var current_bg_color = '#fff';

var bucket_url = 'https://s3.amazonaws.com/lilscreensharetest/';

setInterval(check_for_new_image, 1000);

function check_for_new_image() {
	var todayHours = new Date().getHours();
	var todayMinutes = new Date().getMinutes();

	// Between 11:00AM and 11:05AM display big red "SCRUM" image instead of regular image
	if (todayHours === 11 && todayMinutes >= 00 && todayMinutes < 05) {
		current_filename = "./gold_scrum.gif";
		$('#image-container').attr("src", current_filename);
		current_bg_color = "#242424"
		$('body').css('background-color', current_bg_color);
	} else {
		$.ajax({
			dataType: "json",
			url: bucket_url + 'current.json',
			cache: false,
			success: function(data) {
				if(window.location.hash === '#racehorse') {
					if (data.hasOwnProperty("racehorse") && data['racehorse'].url !== current_filename) {
						current_filename = bucket_url + data['racehorse'].url;
						$('#image-container').attr("src", current_filename);
					}

				}

				if(window.location.hash === '#banana') {
					if (data.hasOwnProperty("banana") && data['banana'].url !== current_filename) {
						current_filename = bucket_url + data['banana'].url;
						$('#image-container').attr("src", current_filename);
					}
				}

				if(window.location.hash === '#icecream') {
					if (data.hasOwnProperty("icecream") && data['icecream'].url !== current_filename) {
						current_filename = bucket_url + data['icecream'].url;
						$('#image-container').attr("src", current_filename);
					}
				}
			}
		});
	}
}
