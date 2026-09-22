$(document).ready(function () {
    const table = $('#proofsTable').DataTable({
        ajax: {
            url: '/api/proofs',
            dataSrc: ''
        },
        columns: [
            { data: 'id' },
            { data: 'type_of_proof' },
            { data: 'lot_no' },
            { data: 'date' },
            { data: 'proof_result_no' },
            { data: 'store' },
            { data: 'quantity' },
            { data: 'proof_sample_size' },
            {
                data: 'tests',
                render: function (data, type, row) {
                    return `<span class="badge bg-secondary">${data ? data.length : 0} Tests</span>`;
                }
            },
            {
                data: null,
                render: function (data, type, row) {
                    return `<a href="/proof/${row.id}" class="btn btn-sm btn-outline-primary d-flex align-items-center gap-1" style="width: fit-content;">
                        <span class="material-symbols-outlined fs-6">visibility</span> View Results
                    </a>`;
                }
            }
        ],
        order: [[0, 'desc']],
        responsive: true
    });

    $('#addProofForm').on('submit', async function (e) {
        e.preventDefault();

        const errorDiv = $('#formError');
        errorDiv.addClass('d-none').text('');

        const formData = new FormData(this);
        const data = Object.fromEntries(formData.entries());

        // Ensure quantity and sample size are integers
        data.quantity = parseInt(data.quantity);
        data.proof_sample_size = parseInt(data.proof_sample_size);

        try {
            const response = await fetch('/api/proofs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                // Success
                this.reset();
                $('#addProofModal').modal('hide');
                table.ajax.reload();
            } else {
                const resData = await response.json();
                errorDiv.removeClass('d-none').text(resData.detail || 'Failed to add proof.');
            }
        } catch (error) {
            errorDiv.removeClass('d-none').text('Network error. Please try again.');
        }
    });
});
