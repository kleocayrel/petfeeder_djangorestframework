// Feed Control JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Update current date and time
    function updateDateTime() {
        const now = new Date();
        document.getElementById('current-datetime').textContent = now.toLocaleString();
    }
    
    // Update date/time every second
    updateDateTime();
    setInterval(updateDateTime, 1000);
    
    // Update portion value displays with visual feedback
    const manualPortionSlider = document.getElementById('manual-portion');
    const manualPortionValue = document.getElementById('manual-portion-value');
    
    manualPortionSlider.addEventListener('input', function() {
        manualPortionValue.textContent = this.value;
        // Change color based on portion size
        if (this.value <= 3) {
            manualPortionValue.className = 'ms-2 badge bg-success';
        } else if (this.value <= 7) {
            manualPortionValue.className = 'ms-2 badge bg-primary';
        } else {
            manualPortionValue.className = 'ms-2 badge bg-danger';
        }
    });
    
    const schedulePortionSlider = document.getElementById('schedule-portion');
    const schedulePortionValue = document.getElementById('schedule-portion-value');
    
    schedulePortionSlider.addEventListener('input', function() {
        schedulePortionValue.textContent = this.value;
        // Change color based on portion size
        if (this.value <= 3) {
            schedulePortionValue.className = 'ms-2 badge bg-success';
        } else if (this.value <= 7) {
            schedulePortionValue.className = 'ms-2 badge bg-primary';
        } else {
            schedulePortionValue.className = 'ms-2 badge bg-danger';
        }
    });

    // Handle manual feed form submission
    document.querySelector('form[name="manual-feed-form"]').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Create status div with loading spinner
        const statusDiv = document.createElement('div');
        statusDiv.className = 'alert alert-info d-flex align-items-center';
        statusDiv.innerHTML = `
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div>Sending feed command... Please wait while your pet's food is being dispensed.</div>
        `;
        this.insertAdjacentElement('beforebegin', statusDiv);

        // Disable the feed button to prevent multiple submissions
        const feedButton = this.querySelector('button[type="submit"]');
        feedButton.disabled = true;
        feedButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Feeding...';

        const portion = parseInt(this.querySelector('#manual-portion').value);
        const steps = portion * 500; // 200 steps per portion

        const formData = new FormData();
        formData.append('portion', portion);
        formData.append('request_type', 'manual_feed');
        formData.append('steps', steps);
        formData.append('direction', 'clockwise');
        formData.append('microstepping', '8');  // Changed from '16' to '1' for full stepping (maximum torque)
        formData.append('speed', '250');  // Reduced speed for more torque

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        fetch(window.location.href, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            statusDiv.className = data.status === 'success' ? 'alert alert-success' : 'alert alert-danger';
            statusDiv.innerHTML = `<i class="${data.status === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'} me-2"></i> ${data.message || 'Feed command sent successfully!'}`;
            
            // Re-enable the button after response
            feedButton.disabled = false;
            feedButton.textContent = 'Feed Now';
            
            if (data.status === 'success') {
                // Show success message with countdown
                let countdown = 3;
                statusDiv.innerHTML += ` <span class="countdown">(Refreshing in ${countdown}...)</span>`;
                const countdownInterval = setInterval(() => {
                    countdown--;
                    const countdownSpan = statusDiv.querySelector('.countdown');
                    if (countdownSpan) {
                        countdownSpan.textContent = `(Refreshing in ${countdown}...)`;
                    }
                    if (countdown <= 0) {
                        clearInterval(countdownInterval);
                        window.location.reload();
                    }
                }, 1000);
            }
        })
        .catch(error => {
            statusDiv.className = 'alert alert-danger';
            statusDiv.innerHTML = `<i class="fas fa-exclamation-triangle me-2"></i> Error: ${error.message}`;
            
            // Re-enable the button after error
            feedButton.disabled = false;
            feedButton.textContent = 'Feed Now';
        });
    });

    // Handle scheduled feed form submission
    document.querySelector('form[name="schedule-feed-form"]').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Create status div with loading spinner
        const statusDiv = document.createElement('div');
        statusDiv.className = 'alert alert-info d-flex align-items-center';
        statusDiv.innerHTML = `
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div>Adding feeding schedule...</div>
        `;
        this.insertAdjacentElement('beforebegin', statusDiv);

        // Disable the schedule button to prevent multiple submissions
        const scheduleButton = this.querySelector('button[type="submit"]');
        scheduleButton.disabled = true;
        scheduleButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adding...';

        const portion = parseInt(this.querySelector('#schedule-portion').value);
        const time = this.querySelector('#schedule-time').value;

        const formData = new FormData();
        formData.append('request_type', 'schedule_feed');
        formData.append('portion', portion);
        formData.append('time', time);
        
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken,
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            statusDiv.className = data.status === 'success' ? 'alert alert-success' : 'alert alert-danger';
            statusDiv.innerHTML = `<i class="${data.status === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'} me-2"></i> ${data.message || 'Schedule added successfully!'}`;
            
            // Re-enable the button after response
            scheduleButton.disabled = false;
            scheduleButton.textContent = 'Add Schedule';
            
            if (data.status === 'success') {
                // Clear the form
                this.querySelector('#schedule-time').value = '';
                this.querySelector('#schedule-portion').value = '5';
                document.getElementById('schedule-portion-value').textContent = '5';
                document.getElementById('schedule-portion-value').className = 'ms-2 badge bg-primary';
                
                // Show success message with countdown
                let countdown = 3;
                statusDiv.innerHTML += ` <span class="countdown">(Refreshing in ${countdown}...)</span>`;
                const countdownInterval = setInterval(() => {
                    countdown--;
                    const countdownSpan = statusDiv.querySelector('.countdown');
                    if (countdownSpan) {
                        countdownSpan.textContent = `(Refreshing in ${countdown}...)`;
                    }
                    if (countdown <= 0) {
                        clearInterval(countdownInterval);
                        window.location.reload();
                    }
                }, 1000);
            }
        })
        .catch(error => {
            statusDiv.className = 'alert alert-danger';
            statusDiv.innerHTML = `<i class="fas fa-exclamation-triangle me-2"></i> Error: ${error.message}`;
            
            // Re-enable the button after error
            scheduleButton.disabled = false;
            scheduleButton.textContent = 'Add Schedule';
        });
    });
});