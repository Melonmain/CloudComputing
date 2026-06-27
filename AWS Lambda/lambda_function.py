import boto3
import json
import os
import random
import string
from decimal import Decimal

def decimal_default(obj):
    if isinstance(obj, Decimal): return int(obj)
    raise TypeError

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
rooms_table = dynamodb.Table('StadtLandFluss_Rooms')
connections_table = dynamodb.Table('StadtLandFluss_Connections')

# REPLACE THIS with your specific API Gateway Connection URL
API_ENDPOINT = 'https://4dfoguhtth.execute-api.us-east-1.amazonaws.com/prod' 

def broadcast_to_room(room_id, room_state):
    apigw = boto3.client('apigatewaymanagementapi', endpoint_url=API_ENDPOINT)
    response = connections_table.scan()
    active_connections = [item['ConnectionId'] for item in response['Items'] if item.get('RoomID') == room_id]
    
    for conn_id in active_connections:
        try:
            apigw.post_to_connection(ConnectionId=conn_id, Data=json.dumps(room_state, default=decimal_default))
        except Exception as e:
            print(f"Dropping stale connection: {conn_id}")
            connections_table.delete_item(Key={'ConnectionId': conn_id})

def lambda_handler(event, context):
    request_context = event.get('requestContext', {})
    
    # --- PATH 1: SERVE HTML ---
    if 'http' in request_context:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'main.html')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return {"statusCode": 200, "headers": {"Content-Type": "text/html"}, "body": f.read()}
        except FileNotFoundError:
            return {"statusCode": 404, "body": "HTML not found"}

    # --- PATH 2: WEBSOCKET LOGIC ---
    connection_id = request_context.get('connectionId')
    route_key = request_context.get('routeKey')
    if not connection_id: return {'statusCode': 400, 'body': 'Invalid'}

    try:
        if route_key == '$connect':
            connections_table.put_item(Item={'ConnectionId': connection_id})
            return {'statusCode': 200}

        elif route_key == '$disconnect':
            # Retrieve player name AND the dynamic room_id from the connections table
            conn_item = connections_table.get_item(Key={'ConnectionId': connection_id}).get('Item', {})
            player_name = conn_item.get('PlayerName')
            room_id = conn_item.get('RoomID') 
            
            connections_table.delete_item(Key={'ConnectionId': connection_id})
            
            if player_name and room_id:
                room = rooms_table.get_item(Key={'RoomID': room_id}).get('Item')
                if room and player_name in room.get('players', {}):
                    del room['players'][player_name]
                    
                    if len(room['players']) == 0:
                        rooms_table.delete_item(Key={'RoomID': room_id})
                        return {'statusCode': 200}
                    
                    if room.get('host') == player_name:
                        room['host'] = list(room['players'].keys())[0]
                    
                    if room['state'] == 'playing':
                        all_submitted = all(p.get('answers') for p in room['players'].values())
                        if all_submitted:
                            room['state'] = 'review'
                            room['review_index'] = 0
                            
                    rooms_table.put_item(Item=room)
                    broadcast_to_room(room_id, room)
            return {'statusCode': 200}

        # Handle Game Actions
        body_str = event.get('body', '{}')
        if not body_str: return {'statusCode': 200}
        
        body = json.loads(body_str)
        action = body.get('action')
        player_name = body.get('playerName')
        room_id = body.get('roomId') # Extract dynamic room ID sent by the frontend
        
        if not room_id:
            return {'statusCode': 400, 'body': 'Missing Room ID'}

        room = rooms_table.get_item(Key={'RoomID': room_id}).get('Item', {
            'RoomID': room_id, 'state': 'lobby', 'categories': ['Stadt', 'Land', 'Fluss'],
            'players': {}, 'current_letter': '?', 'review_index': 0, 'host': ''
        })

        if action == 'join':
            connections_table.update_item(
                Key={'ConnectionId': connection_id},
                UpdateExpression="SET RoomID = :r, PlayerName = :p",
                ExpressionAttributeValues={':r': room_id, ':p': player_name}
            )
            if player_name and player_name not in room['players']:
                room['players'][player_name] = {'answers': {}}
                if not room.get('host') or room['host'] not in room['players']:
                    room['host'] = player_name
                rooms_table.put_item(Item=room)

        elif action == 'update_categories':
            if player_name == room.get('host'):
                room['categories'] = body.get('categories', room['categories'])
                rooms_table.put_item(Item=room)

        elif action == 'start':
            if player_name == room.get('host'):
                room['state'] = 'playing'
                room['categories'] = body.get('categories', ['Stadt', 'Land', 'Fluss'])
                room['review_index'] = 0
                room['current_letter'] = random.choice(string.ascii_uppercase)
                for p in room['players']: room['players'][p]['answers'] = {}
                rooms_table.put_item(Item=room)

        elif action == 'submit':
            if player_name in room['players']:
                room['players'][player_name]['answers'] = body.get('answers', {})
                all_submitted = all(p.get('answers') for p in room['players'].values())
                if all_submitted and len(room['players']) > 0:
                    room['state'] = 'review'
                    room['review_index'] = 0
                rooms_table.put_item(Item=room)

        elif action == 'next_review':
            if player_name == room.get('host'):
                room['review_index'] += 1
                if room['review_index'] >= len(room['categories']):
                    room['state'] = 'lobby'
                    for p in room['players']:
                        room['players'][p]['answers'] = {} 
                rooms_table.put_item(Item=room)

        broadcast_to_room(room_id, room)
        return {'statusCode': 200}

    except Exception as e:
        print(f"WebSocket Error: {str(e)}")
        return {'statusCode': 500}