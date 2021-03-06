# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and 
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2017, Baycrest Centre for Geriatric Care ("Baycrest") and others
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
A convenience module for the command interface
.. moduleauthor:: Mihai Andrei <mihai.andrei@codemart.ro>
"""


from tvb.config import SIMULATOR_MODULE, SIMULATOR_CLASS
from tvb.core.adapters.abcadapter import ABCAdapter
from tvb.core.entities.storage import dao

from tvb.core.services.flow_service import FlowService
from tvb.core.services.project_service import ProjectService
from tvb.core.services.user_service import UserService


def list_projects():
    fmt = "%24s %5s"
    print fmt % ('name', 'id')
    for p in dao.get_all_projects():
        print  fmt % (p.name, p.id)


def list_datatypes(project_id):
    fmt = "%24s %16s %5s %32s %12s"
    print fmt % ('type', 'tag', 'id', 'gid', 'date')
    for dt in dao.get_datatypes_in_project(project_id):
        print fmt % (dt.type, dt.user_tag_1, dt.id, dt.gid, dt.create_date)


def datatype_details(id):
    dt = dao.get_datatype_by_id(id)
    print ProjectService().get_datatype_details(dt.gid)


def load_dt(id):
    dt = dao.get_datatype_by_id(id)
    return dao.get_generic_entity(dt.module + '.' + dt.type, id)


def new_project(name):
    usr = UserService.get_administrators()[0]
    proj = ProjectService().store_project(usr, True, None, name=name, description=name, users=[usr])
    return proj


def import_conn_zip(project_id, zip_path):
    project = dao.get_project_by_id(project_id)
    group = dao.get_algorithm_by_module('tvb.adapters.uploaders.zip_connectivity_importer', 'ZIPConnectivityImporter')
    importer = ABCAdapter.build_adapter(group)
    ### Launch Operation
    FlowService().fire_operation(importer, project.administrator, project_id, uploaded=zip_path)


def fire_simulation(project_id=1, **kwargs):
    project = dao.get_project_by_id(project_id)
    flow_service = FlowService()

    # below the holy procedure to launch with the correct parameters taken from the defaults
    stored_adapter = flow_service.get_algorithm_by_module_and_class(SIMULATOR_MODULE, SIMULATOR_CLASS)
    simulator_adapter = ABCAdapter.build_adapter(stored_adapter)
    flatten_interface = simulator_adapter.flaten_input_interface()
    itree_mngr = flow_service.input_tree_manager
    prepared_flatten_interface = itree_mngr.fill_input_tree_with_options(flatten_interface, project.id,
                                                                         stored_adapter.fk_category)
    launch_args = {}
    for entry in prepared_flatten_interface:
        value = entry['default']
        if isinstance(value, dict):
            value = str(value)
        if hasattr(value, 'tolist'):
            value = value.tolist()
        launch_args[entry['name']] = value
    launch_args.update(**kwargs)
    # end of magic

    launched_operation = flow_service.fire_operation(simulator_adapter, project.administrator,
                                                     project.id, **launch_args)[0]
    return launched_operation
