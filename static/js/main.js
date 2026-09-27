
document.addEventListener('DOMContentLoaded', function() {
    // Print helper
    const printBtns = document.querySelectorAll('.btn-print');
    printBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            window.print();
        });
    });

    // Confirmation for destructive date changes
    const confirmForms = document.querySelectorAll('.confirm-action');
    confirmForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if(!confirm("Are you sure you want to perform this action?")) {
                e.preventDefault();
            }
        });
    });
});
