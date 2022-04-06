$(document).ready(function(){
    $('#modal-btn-edit-profile').click(function(){
       $('.ui.modal.profile')
          .modal('show')
        ;
    })
//    $('.delete-comment-button').click(function(){
//       $('.ui.mini.modal.del-comment')
//          .modal('show')
//        ;
//    })
//    $('.update-comment-button').click(function(){
//       $('.ui.modal.update-comment')
//          .modal('show')
//        ;
//    })

})

$('.message .close')
  .on('click', function() {
    $(this)
      .closest('.message')
      .transition('fade')
    ;
  })
;

window.onload = function () {
   window.scrollTo(0, +localStorage.getItem('page_scroll'));
   document.addEventListener('scroll', function () {
      localStorage.setItem('page_scroll', window.pageYOffset);
   });
}

$('.doubling.cards .image').dimmer({
  on: 'hover'
});


