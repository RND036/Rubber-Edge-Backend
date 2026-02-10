# Custom WebSocket authentication middleware for Channels

# JWT WebSocket authentication middleware for Django Channels
from urllib.parse import parse_qs
from channels.auth import AuthMiddlewareStack
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

from rest_framework_simplejwt.authentication import JWTAuthentication
import jwt
from django.conf import settings
from channels.db import database_sync_to_async

User = get_user_model()

class JWTAuthMiddleware:
	"""
	Custom middleware for JWT authentication in Django Channels.
	Falls back to AuthMiddlewareStack if no token is provided.
	"""
	def __init__(self, inner):
		self.inner = inner

	def __call__(self, scope):
		return self.inner(scope)

	async def __call__(self, scope, receive, send):
		query_string = scope.get('query_string', b'').decode()
		query_params = parse_qs(query_string)
		token = None
		if 'token' in query_params:
			token = query_params['token'][0]

		if token:
			try:
				validated_token = UntypedToken(token)
				jwt_auth = JWTAuthentication()
				# Use sync_to_async for user lookup
				user = await database_sync_to_async(jwt_auth.get_user)(validated_token)
				scope['user'] = user
			except (InvalidToken, TokenError, jwt.DecodeError, User.DoesNotExist):
				scope['user'] = AnonymousUser()
		else:
			scope['user'] = AnonymousUser()

		return await self.inner(scope, receive, send)

# Helper to use in ASGI application
def JWTAuthMiddlewareStack(inner):
	return JWTAuthMiddleware(AuthMiddlewareStack(inner))
