var current_filename = '';
var current_bg_color = '#fff';

var bucket_url = 'https://s3.amazonaws.com/lilscreenshare/';

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
					if (data.name !== current_filename) {
						current_filename = data.name;
						$('#image-container').attr("src", bucket_url + current_filename);
					}

					if (data['background-color'] !== current_bg_color) {
						current_bg_color = data['background-color']
						$('body').css('background-color', current_bg_color);
					}
			}
		});
	}
}