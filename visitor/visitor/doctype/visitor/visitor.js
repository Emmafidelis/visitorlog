// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Visitor", {
	refresh(frm) {
		frm.add_custom_button(__("Scan ID"), () => scan_id(frm));

		const can_verify = frappe.user.has_role("Visitor Verifier") || frappe.user.has_role("System Manager");
		if (!frm.doc.__islocal && !frm.doc.ocr_verified && frm.doc.scanned_id_image && frm.doc.ocr_raw_text && can_verify) {
			frm.add_custom_button(__("Verify ID"), () => verify_id(frm)).addClass("btn-primary");
		}

		if (!frm.doc.__islocal && frm.doc.ocr_verified && !frm.doc.badge_number) {
			frm.add_custom_button(__("Assign Badge"), () => assign_badge(frm)).addClass("btn-primary");
		}
	},
});

function scan_id(frm) {
	new frappe.ui.FileUploader({
		doctype: frm.doctype,
		docname: frm.docname,
		fieldname: "scanned_id_image",
		allow_multiple: false,
		allow_toggle_private: false, // ID scans must stay private; don't let the user override it
		make_attachments_public: false,
		allow_take_photo: true, // lets reception snap the ID with the device's own camera, not just pick a file
		restrictions: { allowed_file_types: ["image/*"] },
		on_success(file_doc) {
			frm.set_value("scanned_id_image", file_doc.file_url);
			frappe.dom.freeze(__("Reading ID..."));
			frappe.call({
				method: "visitor.api.ocr.extract_id_details",
				args: { file_url: file_doc.file_url, id_type: frm.doc.id_type },
				callback(r) {
					frappe.dom.unfreeze();
					if (r.message) apply_ocr_result(frm, r.message);
				},
				error() {
					frappe.dom.unfreeze();
				},
			});
		},
	});
}

function apply_ocr_result(frm, result) {
	frm.set_value("ocr_raw_text", result.raw_text);
	frm.set_value("ocr_confidence", result.confidence);
	frm.set_value("ocr_verified", 0);
	frm.set_value("ocr_suggested_json", JSON.stringify(result.fields || {}));

	// Never overwrite something the officer already typed — OCR only fills blanks.
	const fields = result.fields || {};
	if (fields.id_number && !frm.doc.id_number) frm.set_value("id_number", fields.id_number);
	if (fields.first_name && !frm.doc.first_name) frm.set_value("first_name", fields.first_name);
	if (fields.middle_name && !frm.doc.middle_name) frm.set_value("middle_name", fields.middle_name);
	if (fields.last_name && !frm.doc.last_name) frm.set_value("last_name", fields.last_name);

	frappe.show_alert(
		{
			message: __("ID scanned with {0}% confidence — review every field before saving.", [result.confidence]),
			indicator: result.confidence >= 60 ? "green" : "orange",
		},
		7
	);

	warn_if_duplicate_visitor(frm);
}

function warn_if_duplicate_visitor(frm) {
	// Only meaningful while registering a brand-new visitor — an existing
	// record being re-scanned is obviously the same person.
	if (!frm.doc.__islocal || !frm.doc.id_number) return;

	frappe.db
		.get_list("Visitor", {
			filters: { id_number: frm.doc.id_number },
			fields: ["name", "full_name", "status"],
			limit: 1,
		})
		.then((rows) => {
			if (!rows.length) return;
			frappe.msgprint({
				title: __("Possible Duplicate Visitor"),
				indicator: "orange",
				message: __("{0} ({1}) already has a record with this ID number: {2}", [
					rows[0].full_name,
					rows[0].status,
					frappe.utils.get_form_link("Visitor", rows[0].name, true),
				]),
			});
		});
}

function verify_id(frm) {
	frappe.confirm(__("Confirm the scanned details match the physical ID?"), () => {
		frm.call("mark_verified").then(() => {
			frm.reload_doc();
			frappe.show_alert({ message: __("ID verified"), indicator: "green" });
		});
	});
}

function assign_badge(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Assign Badge"),
		fields: [
			{
				fieldname: "qr_code",
				fieldtype: "Link",
				label: __("Available Badge"),
				options: "Visitors Registration Card",
				reqd: 1,
				get_query: () => ({ filters: { status: "Available" } }),
			},
		],
		primary_action_label: __("Assign"),
		primary_action(values) {
			frappe.call({
				method: "visitor.api.badge.assign_badge",
				args: { visitor: frm.doc.name, qr_code: values.qr_code },
				callback() {
					dialog.hide();
					frm.reload_doc();
					frappe.show_alert({ message: __("Badge assigned"), indicator: "green" });
				},
			});
		},
	});
	dialog.show();
}
