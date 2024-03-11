// // script.js
// document.addEventListener('DOMContentLoaded', function() {
//     // Add event listener to all delete buttons
//     var deleteButtons = document.querySelectorAll('.delete-btn');
    
//     deleteButtons.forEach(function(button) {
//         button.addEventListener('click', function(event) {
//             // Prevent the default behavior of the anchor tag
//             event.preventDefault();
            
//             // Extract the file_id from the data attribute
//             var fileId = button.getAttribute('data-file-id');
            
//             // Make an AJAX request to the delete route
//             fetch('/delete/' + fileId, {
//                 method: 'GET'
//             }).then(function(response) {
//                 if (response.ok) {
//                     // Success: HTTP status code 200
//                     console.log("File deletion successful");
//                     // Reload the page after successful deletion
//                     window.location.reload(true);
//                 } else {
//                     // Error: HTTP status code is not 200
//                     console.log("Error deleting file:", response.statusText);
//                 }
//             }).catch(function(error) {
//                 // Network or other errors
//                 console.error('Error deleting file:', error);
//             });
//         });
//     });
// });
