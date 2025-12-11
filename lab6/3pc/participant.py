import random
import logging

# coordinator messages
from const3PC import VOTE_REQUEST, GLOBAL_COMMIT, GLOBAL_ABORT, PREPARE_COMMIT
# participant decissions
from const3PC import LOCAL_SUCCESS, LOCAL_ABORT
# participant messages
from const3PC import VOTE_COMMIT, VOTE_ABORT, NEED_DECISION, READY_COMMIT
# misc constants
from const3PC import TIMEOUT

import stablelog


class Participant:
    """
    Implements a two phase commit participant.
    - state written to stable log (but recovery is not considered)
    - in case of coordinator crash, participants mutually synchronize states
    - system blocks if all participants vote commit and coordinator crashes
    - allows for partially synchronous behavior with fail-noisy crashes
    """

    def __init__(self, chan):
        self.channel = chan
        self.participant = self.channel.join('participant')
        self.stable_log = stablelog.create_log(
            "participant-" + self.participant)
        self.logger = logging.getLogger("vs2lab.lab6.3pc.Participant")
        self.coordinator = {}
        self.all_participants = {}
        self.state = 'NEW'

    @staticmethod
    def _do_work():
        # Simulate local activities that may succeed or not
        return LOCAL_ABORT if random.random() > 2/3 else LOCAL_SUCCESS

    def _enter_state(self, state):
        self.stable_log.info(state)  # Write to recoverable persistant log file
        self.logger.info("Participant {} entered state {}."
                         .format(self.participant, state))
        self.state = state

    def init(self):
        self.channel.bind(self.participant)
        self.coordinator = self.channel.subgroup('coordinator')
        self.all_participants = self.channel.subgroup('participant')
        self._enter_state('INIT')  # Start in local INIT state.

    def run(self):
        #Phase 1b
        # Wait for start of joint commit
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)
        decision = ""

        if not msg:  # Crashed coordinator - give up entirely
            # decide to locally abort (before doing anything)
            self._enter_state('ABORT')

        else:  # Coordinator requested to vote, joint commit starts
            assert msg[1] == VOTE_REQUEST

            # Firstly, come to a local decision
            decision = self._do_work()  # proceed with local activities

            # If local decision is negative,
            # then vote for abort and quit directly
            if decision == LOCAL_ABORT:
                self.channel.send_to(self.coordinator, VOTE_ABORT)
                self._enter_state('ABORT')

            # If local decision is positive,
            # we are ready to proceed the joint commit
            else:
                assert decision == LOCAL_SUCCESS
                self._enter_state('READY')

                # Notify coordinator about local commit vote
                self.channel.send_to(self.coordinator, VOTE_COMMIT)

            #Phase 2b
            # Wait for coordinator prepare commit
            msg = self.channel.receive_from(self.coordinator, TIMEOUT)
            if not msg:
                self.handleCoordinatorCrash()

            elif msg[1] == GLOBAL_ABORT:
                self._enter_state('ABORT')

            else:
                assert msg[1] == PREPARE_COMMIT
                self._enter_state('PRECOMMIT')
                self.channel.send_to(self.coordinator, READY_COMMIT)

                #Phase 3b
                msg = self.channel.receive_from(self.coordinator, TIMEOUT)
                if not msg:
                    self.handleCoordinatorCrash()

                else:
                    assert msg[1] in [GLOBAL_COMMIT]
                    self._enter_state('COMMIT')



                """ # Wait for coordinator to notify the final outcome
                msg = self.channel.receive_from(self.coordinator, TIMEOUT)

                if not msg:  # Crashed coordinator
                    # Ask all processes for their decisions
                    self.channel.send_to(self.all_participants, NEED_DECISION)
                    while True:
                        msg = self.channel.receive_from_any()
                        # If someone reports a final decision,
                        # we locally adjust to it
                        if msg[1] in [
                                GLOBAL_COMMIT, GLOBAL_ABORT, LOCAL_ABORT]:
                            decision = msg[1]
                            break

                else:  # Coordinator came to a decision
                    decision = msg[1]

        # Change local state based on the outcome of the joint commit protocol
        # Note: If the protocol has blocked due to coordinator crash,
        # we will never reach this point
        if decision == GLOBAL_COMMIT:
            self._enter_state('COMMIT')
        else:
            assert decision in [GLOBAL_ABORT, LOCAL_ABORT]
            self._enter_state('ABORT') """


        """ # Help any other participant when coordinator crashed
        num_of_others = len(self.all_participants) - 1
        while num_of_others > 0:
            num_of_others -= 1
            msg = self.channel.receive_from(self.all_participants, TIMEOUT * 2)
            if msg and msg[1] == NEED_DECISION:
                self.channel.send_to({msg[0]}, decision) """


        return "Participant {} terminated in state {}. Local Decission {}".format(self.participant, self.state, decision)
    

    def handleCoordinatorCrash(self):
        newCoordinator = min(self.all_participants)
        self.coordinator = {newCoordinator}
        self.all_participants.remove(newCoordinator)
        
        if newCoordinator == self.participant: # I am the new coordinator
            self.logger.info("Participant {} is the new coordinator.".format(self.participant))

            # set state based on current state
            if self.state == 'READY':
                self._enter_state('WAIT')
            
            self.channel.send_to(self.all_participants, self.state) # send state to all participants

            # collect states from all participants
            states = []
            yet_to_receive = list(self.all_participants)
            while len(yet_to_receive) > 0:
                msg = self.channel.receive_from(self.all_participants, TIMEOUT)
                states.append(msg[1])
                yet_to_receive.remove(msg[0])


            # decide new global state
            if self.state == 'ABORT' or self.state == 'COMMIT':
                return # already decided and synced
            elif self.state == 'WAIT': #'ABORT' in states or
                self._enter_state('ABORT')
                self.channel.send_to(self.all_participants, GLOBAL_ABORT)
            else: #if all(s in ['PRECOMMIT', 'COMMIT', 'READY'] for s in states):
                self._enter_state('COMMIT')
                self.channel.send_to(self.all_participants, GLOBAL_COMMIT)


        else: # wait for new coordinator messages
            msg = self.channel.receive_from(self.coordinator, TIMEOUT * 2)
            if not msg: # if global commit reaches just a few participants
                self.handleCoordinatorCrash()

            coordinator_state = msg[1]

            if self.state == 'ABORT': # I already aborted
                pass
            elif coordinator_state == 'COMMIT':
                self._enter_state(coordinator_state)
            elif coordinator_state == 'ABORT':
                self._enter_state('ABORT')
            elif coordinator_state == 'PRECOMMIT' and self.state not in ['COMMIT', 'ABORT']: # if coordinator is PRECOMMIT commit
                self._enter_state('PRECOMMIT')
            
            # if coordinator is WAIT send the state so coordinator can decide
            # ready & precommit -> commit, abort -> abort
            self.channel.send_to(self.coordinator, self.state)

            if self.state in ['COMMIT', 'ABORT']:
                return # already decided and synced
            
            # receive final decision from new coordinator
            msg = self.channel.receive_from(self.coordinator, TIMEOUT * 2)
            finalState = msg[1]
            if finalState == GLOBAL_COMMIT:
                self._enter_state('COMMIT')
            elif finalState == GLOBAL_ABORT:
                self._enter_state('ABORT')

            pass
        