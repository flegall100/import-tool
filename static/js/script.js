// Tab switching functionality
document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', function() {
        // Remove active class from all tabs and panes
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        
        // Add active class to clicked tab
        this.classList.add('active');
        
        // Show corresponding pane
        const targetTab = this.getAttribute('data-tab');
        document.getElementById(targetTab).classList.add('active');
    });
});



// Modular comparison table generator - reusable across tabs
function generateComparisonTable(fieldConfig, sourceData, targetData, sourceStoreName, targetStoreName) {
                            let table = `
                    <table class="table">
                        <thead>
                            <tr>
                                <th style="width: 25px;">Field</th>
                                <th style="width: 30%;" class="text-center">
                                    ${sourceStoreName}
                                </th>
                                <th style="width: 25px;" class="text-center">
                                    Transfer
                                </th>
                                <th style="width: 25px;" class="text-center">
                                    Sync
                                </th>
                                <th style="width: 30%;" class="text-center">
                                    ${targetStoreName}
                                </th>
                            </tr>
                        </thead>
            <tbody>
    `;
    
    fieldConfig.forEach(function(field) {
        let sourceValue = sourceData[field.key];
        let targetValue = targetData[field.key];
        
        // Generate source display (read-only, muted style)
        let sourceDisplay = generateSourceDisplay(sourceValue, field);
        
        // Generate target input (editable)
        let targetInput = generateTargetInput(targetValue, field);
        
        // Generate transfer button
        let transferButton = `
            <div class="text-center">
                <button type="button" class="btn btn-sm btn-outline-success transfer-field-btn" 
                        data-field="${field.key}" title="Transfer this field from source to target">
                    →
                </button>
            </div>
        `;
        
        // Generate sync checkbox
        let syncCheckbox = `
            <div class="text-center">
                <div class="form-check d-inline-block">
                    <input class="form-check-input sync-checkbox" type="checkbox" 
                           id="sync_${field.key}" name="sync_${field.key}" 
                           data-field="${field.key}" checked>
                    <label class="form-check-label small" for="sync_${field.key}">
                        Sync
                    </label>
                </div>
            </div>
        `;
        
        table += `
            <tr class="field-row" data-field="${field.key}">
                <td class="fw-bold text-muted">${field.label}</td>
                <td class="source-cell">${sourceDisplay}</td>
                <td class="transfer-cell">${transferButton}</td>
                <td class="sync-cell">${syncCheckbox}</td>
                <td class="target-cell">${targetInput}</td>
            </tr>
        `;
    });
    
    table += '</tbody></table>';
    return table;
}

// Generate read-only source display with muted styling
function generateSourceDisplay(value, field) {
    if (!value || (Array.isArray(value) && value.length === 0)) {
        return '<em class="text-muted">No data</em>';
    }
    
    switch (field.type) {
        case 'json':
            // Special handling for custom_fields to show as a table
            console.log('DEBUG: JSON field detected', field.key, 'value:', value, 'isArray:', Array.isArray(value));
            if (field.key === 'custom_fields' && Array.isArray(value) && value.length > 0) {
                let tableHtml = `
                    <div class="custom-fields-table">
                        <table class="table table-sm table-bordered">
                            <thead class="table-light">
                                <tr>
                                    <th style="width: 40%;">Field Name</th>
                                    <th style="width: 60%;">Value</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                value.forEach(customField => {
                    let fieldName = customField.name || 'Unknown';
                    let fieldValue = customField.value || '';
                    // Show full values without truncation
                    let displayValue = fieldValue;
                    
                    tableHtml += `
                        <tr>
                            <td class="fw-bold text-primary">${$('<div>').text(fieldName).html()}</td>
                            <td>${$('<div>').text(displayValue).html()}</td>
                        </tr>
                    `;
                });
                
                tableHtml += `
                            </tbody>
                        </table>
                        <small class="text-muted">${value.length} custom field(s)</small>
                    </div>
                `;
                
                return tableHtml;
            } else if (field.key === 'custom_fields') {
                return '<em class="text-muted">No custom fields</em>';
            }
            
            // Default JSON handling for other fields
            try {
                let jsonStr = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
                return `<div class="json-display">${$('<div>').text(jsonStr).html()}</div>`;
            } catch (e) {
                return `<div class="text-muted">Invalid JSON data</div>`;
            }
            
        case 'textarea':
            let truncated = value.length > 200 ? value.substring(0, 200) + '...' : value;
            return `<div class="pre-content">${$('<div>').text(truncated).html()}</div>`;
            
        case 'number':
            return `<span class="text-dark" style="font-family: monospace;">${parseFloat(value).toLocaleString()}</span>`;
            
        default:
            // Truncate long text values
            let displayValue = value.toString();
            if (displayValue.length > 150) {
                displayValue = displayValue.substring(0, 150) + '...';
            }
            return `<span class="text-dark">${$('<div>').text(displayValue).html()}</span>`;
    }
}

// Generate editable target input
function generateTargetInput(value, field) {
    let inputHtml = '';
    let displayValue = value || '';
    
    switch (field.type) {
        case 'json':
            // Special handling for custom_fields to show as an editable table
            if (field.key === 'custom_fields') {
                let customFields = Array.isArray(value) ? value : [];
                
                inputHtml = `
                    <div class="custom-fields-editor">
                        <table class="table table-bordered">
                            <thead class="table-light">
                                <tr>
                                    <th>Field Name</th>
                                    <th>Value</th>
                                    <th style="width: 100px;">Action</th>
                                </tr>
                            </thead>
                            <tbody class="custom-fields-tbody">
                `;
                
                customFields.forEach((customField, index) => {
                    let isExisting = customField.id ? true : false;
                    let statusBadge = isExisting 
                        ? '<span class="badge bg-secondary" style="font-size: 9px;">EXISTING</span>' 
                        : '<span class="badge bg-success" style="font-size: 9px;">NEW</span>';
                    
                    inputHtml += `
                        <tr class="custom-field-row" data-index="${index}">
                            <td>
                                <input type="text" class="form-control custom-field-name" 
                                       value="${customField.name || ''}" placeholder="Field name...">
                                ${statusBadge}
                                <input type="hidden" class="custom-field-id" value="${customField.id || ''}">
                            </td>
                            <td>
                                <input type="text" class="form-control custom-field-value" 
                                          placeholder="Field value..." value="${customField.value || ''}">
                            </td>
                            <td class="text-center">
                                <button type="button" class="btn btn-sm btn-outline-danger remove-custom-field" title="Remove field">
                                    ×
                                </button>
                            </td>
                        </tr>
                    `;
                });
                
                inputHtml += `
                            </tbody>
                        </table>
                        <button type="button" class="btn btn-sm btn-outline-primary add-custom-field">
                            + Add Custom Field
                        </button>
                        <input type="hidden" name="${field.key}" class="custom-fields-hidden" value="${JSON.stringify(customFields)}">
                        <div class="mt-2">
                            <small class="text-muted">
                                <strong>EXISTING</strong> fields will update the original custom field in BigCommerce. 
                                <strong>NEW</strong> fields will create new custom fields. Changes are saved automatically.
                            </small>
                        </div>
                    </div>
                `;
            } else {
                // Default JSON handling for other fields
                let jsonStr = '';
                try {
                    jsonStr = typeof displayValue === 'string' ? displayValue : JSON.stringify(displayValue, null, 2);
                } catch (e) {
                    jsonStr = JSON.stringify(displayValue || {}, null, 2);
                }
                inputHtml = `<textarea class="form-control form-control-sm" name="${field.key}" rows="4" placeholder="Enter JSON data...">${jsonStr}</textarea>`;
            }
            break;
            
        case 'textarea':
            inputHtml = `<textarea class="form-control form-control-sm" name="${field.key}" rows="3" placeholder="Enter ${field.label.toLowerCase()}...">${displayValue}</textarea>`;
            break;
            
        case 'number':
            let numValue = displayValue ? parseFloat(displayValue) : '';
            inputHtml = `<input type="number" step="any" class="form-control form-control-sm" name="${field.key}" value="${numValue}" placeholder="0.00">`;
            break;
            
        default:
            inputHtml = `<input type="text" class="form-control form-control-sm" name="${field.key}" value="${displayValue}" placeholder="Enter ${field.label.toLowerCase()}...">`;
    }
    
    return inputHtml;
}

// Handle sync checkbox changes
function handleSyncToggle(checkbox) {
    let fieldKey = checkbox.data('field');
    let targetCell = checkbox.closest('tr').find('.target-cell');
    let isChecked = checkbox.is(':checked');
    
    if (isChecked) {
        targetCell.find('input, textarea').prop('disabled', false).removeClass('opacity-50');
        targetCell.removeClass('disabled');
    } else {
        targetCell.find('input, textarea').prop('disabled', true).addClass('opacity-50');
        targetCell.addClass('disabled');
    }
    
    updateSyncSummary();
}

// Update sync summary display
function updateSyncSummary() {
    let totalFields = $('.sync-checkbox').length;
    let checkedFields = $('.sync-checkbox:checked').length;
    
    if (checkedFields === totalFields) {
        $('#sync-summary').text('All fields selected for sync');
    } else if (checkedFields === 0) {
        $('#sync-summary').text('No fields selected for sync');
    } else {
        $('#sync-summary').text(`${checkedFields} of ${totalFields} fields selected for sync`);
    }
}

// jQuery functionality
$(function() {
// Compare form logic
$('#compare-form').on('submit', function(e) {
    e.preventDefault();
        $('#compare-result').html('<div class="loading"><div class="loading-spinner"></div><p class="mt-3 text-muted fw-500">Loading product comparison...</p></div>');
    
    var formData = {
        store_a: $('#source-store').val(),
        store_b: $('#target-store').val(),
        sku_a: $('#sku-source').val(),
        sku_b: $('#sku-target').val()
    };
    
    $.post('/compare', formData, function(data) {
        if (data.success) {
            let a = data.product_a || {};
            let b = data.product_b || {};
                
                // Modular field configuration for reuse across tabs
                let fieldConfig = [
                    {key: 'name', label: 'Name', type: 'text'},
                    {key: 'price', label: 'Price', type: 'number'},
                    {key: 'brand', label: 'Brand', type: 'text'},
                    {key: 'description', label: 'Description', type: 'textarea'},
                    {key: 'sku', label: 'SKU', type: 'text'},
                    {key: 'mpn', label: 'MPN', type: 'text'},
                    {key: 'upc', label: 'UPC', type: 'text'},
                    {key: 'gtin', label: 'GTIN', type: 'text'},
                    {key: 'weight', label: 'Weight', type: 'number'},
                    {key: 'width', label: 'Width', type: 'number'},
                    {key: 'height', label: 'Height', type: 'number'},
                    {key: 'depth', label: 'Depth', type: 'number'},
                    {key: 'custom_fields', label: 'Custom Fields', type: 'json'}
            ];
                
                // Generate modular comparison table
                let table = generateComparisonTable(fieldConfig, a, b, data.store_a_name, data.store_b_name);
                
                // Check for warnings (e.g., target product doesn't exist)
                let warningHtml = '';
                if (data.warning) {
                    warningHtml = `<div class="alert alert-warning" style="margin-bottom: 20px;">
                        <strong>Notice:</strong> ${data.warning}
                    </div>`;
                }
                
                // Create sticky container with scrollable table and fixed button
                let container = `
                    <div class="comparison-container">
                        ${warningHtml}
                        <div class="sync-controls">
                            <div class="sync-controls-header">
                                                                            <div class="sync-controls-left">
                                        <span class="fw-bold">Sync Controls:</span>
                                        <button type="button" class="btn btn-outline" id="select-all-sync">
                                            Select All
                                        </button>
                                        <button type="button" class="btn btn-outline" id="deselect-all-sync">
                                            Deselect All
                                        </button>
                                        <button type="button" class="btn btn-success" id="transfer-all-btn">
                                            Transfer All →
                                        </button>
                        </div>
                                    <div class="sync-controls-right">
                                        <span id="sync-summary">All fields selected for sync</span>
                            </div>
                        </div>
                        </div>
                        <div class="table-scroll">
                            ${table}
                        </div>
                                                            <div class="sticky-button">
                                <button type="button" class="btn btn-primary btn-lg" id="update-target-btn">
                                    ${data.product_b ? 'Update Target Store' : 'Create Product in Target Store'}
                                </button>
                            </div>
                    </div>
                `;
                $('#compare-result').html(container);
                
                // FORCE CHECKBOXES TO BE CHECKED (workaround for state issue)
                $('.sync-checkbox').prop('checked', true);
                } else {
                // Show specific error message from backend
                $('#compare-result').html('<div class="alert alert-danger"><strong>Error:</strong> ' + (data.error || 'Compare failed.') + '</div>');
        }
    }).fail(function(xhr) {
            $('#compare-result').html('<div class="alert alert-danger">' + (xhr.responseJSON?.error || 'Compare failed.') + '</div>');
    });
});

// Pull Target Info button
$('#pull-target-info').on('click', function() {
    var targetStore = $('#target-store').val();
    var skuTarget = $('#sku-target').val();
    
    if (!skuTarget) {
        alert('Please enter a Target SKU first');
        return;
    }
    
        $('#compare-result').html('<div class="loading"><div class="loading-spinner"></div><p class="mt-3 text-muted fw-500">Loading target store info...</p></div>');
    
    $.post('/get_product', {
        store: targetStore,
        sku: skuTarget
    }, function(data) {
        if (data.success) {
            var product = data.product;
            var storeName = $('#target-store option:selected').text();
            
            var html = '<div class="alert alert-info">';
                html += '<h6>Target Store Product Info:</h6>';
                html += '<div class="d-flex flex-wrap gap-3">';
                html += '<div><strong>Name:</strong> ' + (product.name || 'N/A') + '</div>';
                html += '<div><strong>SKU:</strong> ' + (product.sku || 'N/A') + '</div>';
                html += '<div><strong>Price:</strong> ' + (product.price || 'N/A') + '</div>';
                html += '<div><strong>Brand:</strong> ' + (product.brand || 'N/A') + '</div>';
            html += '</div></div>';
            
            $('#compare-result').html(html);
        } else {
                $('#compare-result').html('<div class="alert alert-warning">' + (data.error || 'Product not found in Target Store') + '</div>');
        }
    }).fail(function(xhr) {
            $('#compare-result').html('<div class="alert alert-danger">' + (xhr.responseJSON?.error || 'Failed to fetch Target Store info') + '</div>');
    });
});

// Single import form
$('#single-import-form').on('submit', function(e) {
    e.preventDefault();
        $('#single-import-result').html('<div class="loading"><div class="loading-spinner"></div><p class="mt-3 text-muted fw-500">Importing product...</p></div>');
    $.post('/import', $(this).serialize(), function(data) {
        if (data.success) {
                $('#single-import-result').html('<div class="alert alert-success">' + data.message + '</div>');
        } else {
                $('#single-import-result').html('<div class="alert alert-danger">' + (data.error || 'Import failed.') + '</div>');
        }
    }).fail(function(xhr) {
            $('#single-import-result').html('<div class="alert alert-danger">' + (xhr.responseJSON?.error || 'Import failed.') + '</div>');
    });
});

// Batch import form
$('#batch-import-form').on('submit', function(e) {
    e.preventDefault();
        $('#batch-import-result').html('<div class="loading"><div class="loading-spinner"></div><p class="mt-3 text-muted fw-500">Processing batch import...</p></div>');
    var formData = new FormData(this);
    $.ajax({
        url: '/batch_import',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(data) {
            if (data.success) {
                    let html = '<div class="alert alert-info">Batch import results:</div><div class="list-group">';
                data.results.forEach(function(res) {
                    if (res.success) {
                            html += '<div class="list-group-item list-group-item-success">' + res.sku + ': Success</div>';
                    } else {
                            html += '<div class="list-group-item list-group-item-danger">' + res.sku + ': Failed' + (res.error ? ' (' + res.error + ')' : '') + '</div>';
                    }
                });
                html += '</div>';
                $('#batch-import-result').html(html);
            } else {
                    $('#batch-import-result').html('<div class="alert alert-danger">' + (data.error || 'Batch import failed.') + '</div>');
            }
        },
        error: function(xhr) {
                $('#batch-import-result').html('<div class="alert alert-danger">' + (xhr.responseJSON?.error || 'Batch import failed.') + '</div>');
        }
    });
});

    // Sync checkbox functionality
    $(document).on('change', '.sync-checkbox', function() {
        handleSyncToggle($(this));
    });
    
    // Select All / Deselect All functionality
    $(document).on('click', '#select-all-sync', function() {
        $('.sync-checkbox').prop('checked', true).trigger('change');
        updateSyncSummary();
    });
    
    $(document).on('click', '#deselect-all-sync', function() {
        $('.sync-checkbox').prop('checked', false).trigger('change');
        updateSyncSummary();
    });
    
    // Transfer All functionality
    $(document).on('click', '#transfer-all-btn', function() {
        // Transfer all values from source (Product A) to target (Product B)
        $('.field-row').each(function() {
            var row = $(this);
            var sourceCell = row.find('.source-cell');
            var targetCell = row.find('.target-cell');
            var targetInput = targetCell.find('input, textarea');
            
            if (targetInput.length > 0) {
                // Get the source value based on the field type
                var sourceValue = getSourceValue(sourceCell, targetInput);
                if (sourceValue !== null && sourceValue !== undefined) {
                    targetInput.val(sourceValue);
                    // Trigger change event for any listeners
                    targetInput.trigger('change');
                }
            }
        });
        
        // Also handle custom fields if they exist
        transferCustomFields();
        
        // Show confirmation message
        showTransferConfirmation();
    });
    
    // Individual field transfer functionality
    $(document).on('click', '.transfer-field-btn', function() {
        var button = $(this);
        var fieldKey = button.data('field');
        var row = button.closest('.field-row');
        var sourceCell = row.find('.source-cell');
        var targetCell = row.find('.target-cell');
        var targetInput = targetCell.find('input, textarea');
        
        if (targetInput.length > 0) {
            // Get the source value based on the field type
            var sourceValue = getSourceValue(sourceCell, targetInput);
            if (sourceValue !== null && sourceValue !== undefined) {
                // For images, getSourceValue handles everything internally
                if (sourceValue !== true) {
                    targetInput.val(sourceValue);
                    // Trigger change event for any listeners
                    targetInput.trigger('change');
                }
                
                // Show brief visual feedback
                button.removeClass('btn-outline-success').addClass('btn-success');
                setTimeout(function() {
                    button.removeClass('btn-success').addClass('btn-outline-success');
                }, 500);
            }
        }
        
        // Handle custom fields for this specific field if it's custom fields
        if (fieldKey === 'custom_fields') {
            transferCustomFields();
        }
    });


// Custom fields editor handlers
$(document).on('click', '.add-custom-field', function(e) {
    e.preventDefault();
    var tbody = $(this).closest('.custom-fields-editor').find('.custom-fields-tbody');
    var newIndex = tbody.find('tr').length;
    
    var newRow = `
        <tr class="custom-field-row" data-index="${newIndex}">
            <td>
                <input type="text" class="form-control custom-field-name" 
                       value="" placeholder="Field name...">
                <span class="badge bg-success" style="font-size: 9px;">NEW</span>
                <input type="hidden" class="custom-field-id" value="">
            </td>
            <td>
                <input type="text" class="form-control custom-field-value" 
                          placeholder="Field value...">
            </td>
            <td class="text-center">
                <button type="button" class="btn btn-sm btn-outline-danger remove-custom-field" title="Remove field">
                    ×
                </button>
            </td>
        </tr>
    `;
    
    tbody.append(newRow);
    updateCustomFieldsHidden($(this).closest('.custom-fields-editor'));
});

$(document).on('click', '.remove-custom-field', function(e) {
    e.preventDefault();
    var row = $(this).closest('tr');
    var editor = $(this).closest('.custom-fields-editor');
    row.remove();
    updateCustomFieldsHidden(editor);
});

$(document).on('input', '.custom-field-name, .custom-field-value', function() {
    var editor = $(this).closest('.custom-fields-editor');
    updateCustomFieldsHidden(editor);
});

    // Update Target Store button click
    $(document).on('click', '#update-target-btn', function(e) {
        e.preventDefault();
        

        
        // COLLECT SYNC FIELDS IMMEDIATELY (before confirmation dialog destroys them)
        var syncFields = [];
        var formDataToSend = new FormData();
        
        $('.sync-checkbox:checked').each(function() {
            var fieldName = $(this).data('field');
            syncFields.push(fieldName);
            formDataToSend.append('sync_' + fieldName, 'on');
        });
        

        
        if (syncFields.length === 0) {
            $('#compare-result').html('<div class="alert alert-warning">Please select at least one field to sync.</div>');
            return;
        }
        
        // Collect field values BEFORE showing confirmation dialog
        $('.target-cell input, .target-cell textarea').each(function() {
            var name = $(this).attr('name');
            if (name && $(this).closest('tr').find('.sync-checkbox:checked').length > 0) {
                formDataToSend.append(name, $(this).val());
            }
        });
        
        // Add comparison data
        formDataToSend.append('store_a', $('#source-store').val());
        formDataToSend.append('store_b', $('#target-store').val());
        formDataToSend.append('sku_a', $('#sku-source').val());
        formDataToSend.append('sku_b', $('#sku-target').val());
        
        // Store the form data globally for use after confirmation
        window.preparedFormData = formDataToSend;
        
        // Get store names
        var sourceStoreName = $('#source-store option:selected').text();
        var targetStoreName = $('#target-store option:selected').text();
        var sourceSku = $('#sku-source').val();
        var targetSku = $('#sku-target').val();
        
        // Create confirmation dialog
        var confirmationHtml = `
            <div class="alert alert-warning" style="border-left: 4px solid #ffc107;">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <h5 style="margin: 0; color: #856404;">Confirm Update</h5>
                </div>
                <p style="margin-bottom: 15px; color: #856404;">
                    You are about to update the following fields from <strong>${sourceStoreName}</strong> to <strong>${targetStoreName}</strong>:
                </p>
                <div style="background: #fff3cd; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                    <p style="margin: 0 0 10px 0; font-weight: 600; color: #856404;">Fields to be updated:</p>
                    <ul style="margin: 0; padding-left: 20px; color: #856404;">
                        ${syncFields.map(field => `<li>${field.charAt(0).toUpperCase() + field.slice(1)}</li>`).join('')}
                    </ul>
                </div>
                <p style="margin-bottom: 20px; color: #856404;">
                    <strong>Source:</strong> ${sourceSku} (${sourceStoreName})<br>
                    <strong>Target:</strong> ${targetSku} (${targetStoreName})
                </p>
                                            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button type="button" class="btn btn-success" id="confirm-update">
                            Yes, Update Target Store
                        </button>
                        <button type="button" class="btn btn-outline" id="cancel-update">
                            Cancel
                        </button>
                    </div>
            </div>
        `;
        
        $('#compare-result').html(confirmationHtml);
    });
    
    // Handle confirmation button
    $(document).on('click', '#confirm-update', function() {
        // Show loading state
        $('#compare-result').html('<div class="loading"><div class="loading-spinner"></div><p class="mt-3 text-muted fw-500">Updating target store...</p></div>');
        
        // Use the pre-collected form data (collected before confirmation dialog)
        var formData = window.preparedFormData;
        
        if (!formData) {
            $('#compare-result').html('<div class="alert alert-danger">Error: Form data not prepared properly.</div>');
            return;
        }
        
        // Submit via AJAX
        $.ajax({
            url: '/update_target',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(data) {
                if (data.success) {
                    $('#compare-result').html('<div class="alert alert-success">' + (data.message || 'Target store updated successfully!') + '</div>');
                } else {
                    $('#compare-result').html('<div class="alert alert-danger">' + (data.error || 'Failed to update target store.') + '</div>');
                }
            },
            error: function(xhr) {
                $('#compare-result').html('<div class="alert alert-danger">' + (xhr.responseJSON?.error || 'Failed to update target store.') + '</div>');
            }
        });
    });
    
    // Handle cancel button
    $(document).on('click', '#cancel-update', function() {
        // Re-run the comparison to restore the table
        $('#compare-form').submit();
});


});


// Helper functions for transfer functionality
function updateCustomFieldsHidden(editor) {
    var customFields = [];
    
    editor.find('.custom-fields-tbody tr').each(function() {
        var name = $(this).find('.custom-field-name').val().trim();
        var value = $(this).find('.custom-field-value').val().trim();
        var id = $(this).find('.custom-field-id').val().trim();
        
        if (name || value) { // Only add if name or value is not empty
            var fieldData = {
                name: name,
                value: value
            };
            
            // Preserve the original ID if it exists (for updating existing fields)
            if (id) {
                fieldData.id = parseInt(id);
            }
            
            customFields.push(fieldData);
        }
    });
    
    editor.find('.custom-fields-hidden').val(JSON.stringify(customFields));
}

function getSourceValue(sourceCell, targetInput) {
    
    // For regular text inputs and textareas
    if (targetInput.is('input[type="text"], input[type="number"], textarea')) {
        var sourceText = sourceCell.text().trim();
        // Remove any extra whitespace and return clean value
        return sourceText === 'N/A' || sourceText === '' ? '' : sourceText;
    }
    
    return null;
}

function transferCustomFields() {
    // Handle custom fields transfer
    var sourceCustomFields = [];
    var targetEditor = $('.custom-fields-editor');
    
    if (targetEditor.length > 0) {
        // Find source custom fields data from table
        var sourceTable = $('.source-cell').find('.custom-fields-table table tbody tr');
        
        if (sourceTable.length > 0) {
            // Extract custom fields from the source table
            sourceTable.each(function() {
                var name = $(this).find('td:first-child').text().trim();
                var value = $(this).find('td:last-child').text().trim();
                
                if (name && value) {
                    sourceCustomFields.push({
                        name: name,
                        value: value
                    });
                }
            });
            
            // Clear existing custom fields and add source fields
            var tbody = targetEditor.find('.custom-fields-tbody');
            tbody.empty();
            
            sourceCustomFields.forEach(function(field, index) {
                var newRow = `
                    <tr class="custom-field-row" data-index="${index}">
                        <td>
                            <input type="text" class="form-control custom-field-name" 
                                   value="${field.name}" placeholder="Field name...">
                            <span class="badge bg-success" style="font-size: 9px;">NEW</span>
                            <input type="hidden" class="custom-field-id" value="">
                        </td>
                        <td>
                            <input type="text" class="form-control custom-field-value" 
                                      placeholder="Field value..." value="${field.value}">
                        </td>
                        <td class="text-center">
                            <button type="button" class="btn btn-sm btn-outline-danger remove-custom-field" title="Remove field">
                                ×
                            </button>
                        </td>
                    </tr>
                `;
                
                tbody.append(newRow);
            });
            
            updateCustomFieldsHidden(targetEditor);
        }
    }
}

function showTransferConfirmation() {
    // Show a brief confirmation message
    var confirmationHtml = '<div class="alert alert-success alert-dismissible fade show" role="alert">' +
        '<strong>Transfer Complete!</strong> All field values have been copied from the source product to the target product.' +
        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' +
        '</div>';
    
    // Insert the confirmation at the top of the comparison container
    $('.comparison-container').prepend(confirmationHtml);
    
    // Auto-dismiss after 3 seconds
    setTimeout(function() {
        $('.alert-success').fadeOut();
    }, 3000);
} 