document.addEventListener('DOMContentLoaded', function() {
	var form = document.querySelector('form');
	if (form) {
		form.addEventListener('submit', function(e) {
			var pw = form.querySelector('input[type="password"]');
			if (pw && !pw.value) {
				e.preventDefault();
				alert('パスワードを入力してください');
			}
		});
	}
});
