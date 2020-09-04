# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import odoo


def migrate(cr, version):
    """
    Salary Rules can be archived by Odoo S.A. during migration.
    This leaves them archived after the migration, and even un-archiving them
    is not enough because they will then be pointed to a "migrated" structure.

    Unarchiving them first makes it possible for regular upgrade to point them
    to the correct structure.
    """
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    structure = env.ref('l10n_us_hr_payroll.hr_payroll_structure')
    xml_refs = env['ir.model.data'].search([
        ('module', '=', 'l10n_us_hr_payroll'),
        ('model', '=', 'hr.salary.rule'),
    ])
    rule_ids = xml_refs.mapped('res_id')
    rules = env['hr.salary.rule'].browse(rule_ids)
    rules.write({'struct_id': structure.id})
    # other_structure_types = env['hr.payroll.structure.type'].search([
    #     ('name', 'ilike', 'USA Employee'),
    #     ('id', '!=', structure_type.id)
    # ])
    # if other_structure_types:
    #     contracts = env['hr.contract'].search([
    #         ('structure_type_id', 'in', other_structure_types.ids),
    #         ('state', 'in', ('draft', 'open')),  # arbitrary choice not to modify old contracts
    #     ])
    #     if contracts:
    #         contracts.write({'structure_type_id': structure_type.id})
    # structure = env.ref('l10n_us_hr_payroll.hr_payroll_structure')
    # other_structures = env['hr.payroll.structure'].search([
    #     ('name', 'ilike', 'USA Employee'),
    #     ('id', '!=', structure.id)
    # ])
    # if other_structures:
    #
