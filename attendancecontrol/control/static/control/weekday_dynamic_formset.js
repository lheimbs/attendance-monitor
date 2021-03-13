
$('.weekday_form_update').formset({
    prefix: 'week_days',
    addText: 'Add another date',
    addCssClass: 'btn btn-outline-primary',
    addContainerClass: 'weekdays-container',
    deleteText: 'Remove date',
    deleteCssClass: 'btn btn-outline-dark btn-sm',
    deleteContainerClass: 'delete-weekday-container',
    formCssClass: 'dynamic-formset-week_days',
    //formTemplate: $('.empty-weekday-form'),
    hideLastAddForm: true,
});

$('.weekday_form_add').formset({
    prefix: 'week_days',
    addText: 'Add another date',
    addCssClass: 'btn btn-outline-primary',
    addContainerClass: 'weekdays-container',
    deleteText: 'Remove datum',
    deleteCssClass: 'btn btn-outline-dark btn-sm',
    deleteContainerClass: 'delete-weekday-container',
});