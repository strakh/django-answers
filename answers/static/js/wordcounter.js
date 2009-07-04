(function($){
	$.fn.wordCounter = function(){
		this.each(function(){
			var $this = $(this),
			    max = $this.attr('class').match(/max-length-(\d*)/)[1],
			label = $(' <span class="characters"></span>')
						.appendTo($('label[for='+$this.attr('id')+']'));
		function update_count(){
			var chars = max-$this.val().length,
				msg = '';
			if(chars >= 0){
				msg = ' (te quedan '+chars+' letras)';
			}else{
				msg = ' (te pasaste por '+(chars*-1)+' letras)'
				}
				label.html(msg);
			}
			$this.keydown(function(e){
				update_count();
				if($this.val().length >= max && e.keyCode != 8 && e.keyCode != 46){
					return false;
				}
			});
			$this.keyup(update_count);
			update_count();
		});
		return this;
	}
})(jQuery);