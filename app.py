from flask import Flask, request, jsonify
import random
from waitress import serve
import logging
app = Flask(__name__)

# Hacker actions and their probabilities
HACKER_ACTIONS = {
    'Phishing': {'base_probability': 0.90, 'compromise_range': (35, 58)},
    'Virus': {'base_probability': 0.85, 'compromise_range': (48, 82)},
    'Malware': {'base_probability': 0.80, 'compromise_range': (63, 95)},
}
 
# Defender actions and their effects
DEFENDER_ACTIONS = {
    'Firewall': {'compromise_reduction_range': (6, 10), 'hacker_probability_reduction': 0.08},
    'Virus Protection': {'shield_range': (20, 35)},
    'Intrusion Detection': {'revive_range': (45, 68), 'reduction_range': (5, 10)},
    'User Training': {'damage_reduction_range': (10, 30), 'compromise_reduction_range': (6, 15)},
}

# State tracking for each location
location_damage_reduction = {}
location_hacker_probability_reduction = {loc: 0 for loc in [
    'Business', 'Hospital', 'Fire/Police', 'Industrial',
    'University', 'Housing', 'Fort Sam', 'Traffic Lights'
]}

defender_action_cooldowns = {'Intrusion Detection': 0}


def decrement_cooldowns():
    """Decrement cooldowns for defender actions."""
    for action in defender_action_cooldowns:
        if defender_action_cooldowns[action] > 0:
            defender_action_cooldowns[action] -= 1


@app.route('/process_action', methods=['POST'])
def process_action():
    data = request.json
    side = data['side']
    action = data['action']
    location = data['location']
    current_compromise = data.get('current_compromise', 0)

    result = {}

    if side == 'Hacker':
        # Get action details and apply any probability reduction from Firewall
        action_details = HACKER_ACTIONS[action]
        total_probability_reduction = location_hacker_probability_reduction.get(location, 0)
        effective_probability = action_details['base_probability'] - total_probability_reduction

        success = random.random() < effective_probability
        location_hacker_probability_reduction[location] = 0  # Reset after attack

        if success:
            compromise_increase = random.randint(*action_details['compromise_range'])
            reduction = location_damage_reduction.get(location, 0)
            final_increase = max(compromise_increase - reduction, 0)
            location_damage_reduction[location] = 0  # Reset damage reduction

            # Conditional message based on probability reduction
            if total_probability_reduction > 0:
                message = (
                    f'{action} was applied to {location} and increased the compromise by {final_increase}%. '
                    f'Great job landing a successful attack despite the Firewall reducing your probability by '
                    f'{total_probability_reduction * 100:.2f}%.'
                )
            else:
                message = (
                    f'{action} was applied to {location} and increased the compromise by {final_increase}%.'
                )

            result = {
                'action': action,
                'location': location,
                'compromise': final_increase,
                'message': message
            }
        else:
            message = (
                f'{action} failed at {location}, most likely due to previous Firewalls that had been applied. '
            )
            if total_probability_reduction > 0:
                message += (
                    f'The probability for future attacks at {location} was decreased by '
                    f'{total_probability_reduction * 100:.2f}%.'
                )
            result = {
                'action': action,
                'location': location,
                'compromise': 0,
                'message': message
            }

    elif side == 'Defender':
        if action == 'Firewall':
            reduction = random.randint(*DEFENDER_ACTIONS['Firewall']['compromise_reduction_range'])
            applied_value = min(reduction, current_compromise)

            # Stack the hacker probability reduction
            location_hacker_probability_reduction[location] += DEFENDER_ACTIONS['Firewall'][
                'hacker_probability_reduction']
            total_probability_reduction = location_hacker_probability_reduction[location]

            if applied_value == reduction:
                message = (
                    f'Firewall activated at {location}, compromise decreased by {applied_value}%. '
                    f'The probability that the next attack will be successful at {location} was decreased by '
                    f'{total_probability_reduction * 100:.2f}%.'
                )
            else:
                message = (
                    f'Firewall activated at {location}, reducing compromise by {applied_value}%. '
                    f'The full reduction was {reduction}%, but only {applied_value}% could be applied. '
                    f'The probability that the next attack will be successful at {location} was decreased by '
                    f'{total_probability_reduction * 100:.2f}%.'
                )

            result = {
                'action': action,
                'location': location,
                'compromise': -applied_value,
                'message': message
            }

        elif action == 'Intrusion Detection':
            if defender_action_cooldowns['Intrusion Detection'] > 0:
                message = f'Intrusion Detection is on cooldown for {defender_action_cooldowns["Intrusion Detection"]} more rounds.'
                result = {'message': message}
            else:
                revive_amount = random.randint(*DEFENDER_ACTIONS['Intrusion Detection']['revive_range'])
                applied_value = min(revive_amount, current_compromise)

                if applied_value == revive_amount:
                    message = (
                        f'Intrusion Detection revived systems at {location}, decreasing compromise by {applied_value}%.'
                    )
                else:
                    message = (
                        f'Intrusion Detection revived systems at {location}, decreasing compromise by {applied_value}%. '
                        f'The full revive value was {revive_amount}%, but only {applied_value}% could be applied since compromise cannot go below 0.'
                    )

                defender_action_cooldowns['Intrusion Detection'] = 2

                result = {
                    'action': action,
                    'location': location,
                    'compromise': -applied_value,
                    'message': message
                }

        elif action == 'Virus Protection':
            shield = random.randint(*DEFENDER_ACTIONS['Virus Protection']['shield_range'])
            message = f'Virus Protection deployed at {location}, adding a shield of {shield}%.'
            result = {
                'action': action,
                'location': location,
                'shield': shield,
                'compromise': 0,
                'message': message
            }

        elif action == 'User Training':
            reduction = random.randint(*DEFENDER_ACTIONS['User Training']['compromise_reduction_range'])
            applied_value = min(reduction, current_compromise)
            damage_reduction = random.randint(*DEFENDER_ACTIONS['User Training']['damage_reduction_range'])

            location_damage_reduction[location] = location_damage_reduction.get(location, 0) + damage_reduction

            message = (
                f'User Training conducted at {location}, reducing compromise by {applied_value}% and '
                f'mitigating the next attack\'s damage by {damage_reduction}%.'
            )
            result = {
                'action': action,
                'location': location,
                'compromise': -applied_value,
                'message': message
            }

    decrement_cooldowns()
    return jsonify(result)

logging.basicConfig(level=logging.DEBUG, format = '%(asctime)s %(message)s')

if __name__ == '__main__':
    serve(app, host = "127.0.0.1", port=4000)
