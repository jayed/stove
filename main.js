var current_filename = '';
var current_bg_color = '#fff';

var bucket_url = 'https://s3.amazonaws.com/lilscreenshare/';

setInterval(check_for_new_image, 1000);

function check_for_new_image() {		
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