# Copyright (C) 2013 Johnny Vestergaard <jkv@unixcluster.dk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import poplib
from datetime import datetime
import logging

from beeswarm.drones.client.baits.clientbase import ClientBase


logger = logging.getLogger(__name__)


class Pop3(ClientBase):
    def __init__(self, options):
        """
            Initializes common values.

        :param options: A dict containing all options
        """
        super(Pop3, self).__init__(options)

    def start(self):
        """
            Launches a new POP3 client session on the server.
        """

        username = self.options['username']
        password = self.options['password']
        server_host = self.options['server']
        server_port = self.options['port']
        honeypot_id = self.options['honeypot_id']

        session = self.create_session(server_host, server_port, honeypot_id)

        try:
            logger.debug(
                'Sending {0} bait session to {1}:{2}. (bait id: {3})'.format('pop3', server_host, server_port,
                                                                             session.id))
            conn = poplib.POP3(server_host, server_port)

            session.source_port = conn.sock.getsockname()[1]

            banner = conn.getwelcome()
            session.protocol_data['banner'] = banner
            session.did_connect = True

            conn.user(username)
            conn.pass_(password)
            # TODO: Handle failed login
            session.add_auth_attempt('plaintext', True, username=username, password=password)
            session.did_login = True
            session.timestamp = datetime.utcnow()
        # except (poplib.error_proto, h_socket.error) as err:
        except Exception as err:
            logger.debug('Caught exception: {0} ({1})'.format(err, str(type(err))))
        else:
            list_entries = conn.list()[1]
            for entry in list_entries:
                index, octets = entry.split(' ')
                conn.retr(index)
                conn.dele(index)
            logger.debug('Found and deleted {0} messages on {1}'.format(len(list_entries), server_host))
            conn.quit()
            session.did_complete = True
        finally:
            session.all_done = True
            session.end_session()
            if conn:
                try:
                    conn.file.close()
                except Exception:
                    pass
                try:
                    conn.sock.close()
                except Exception:
                    pass
