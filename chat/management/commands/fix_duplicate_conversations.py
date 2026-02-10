# Save this as: chat/management/commands/fix_duplicate_conversations.py
# Create directories if they don't exist:
# chat/management/
# chat/management/__init__.py
# chat/management/commands/
# chat/management/commands/__init__.py

from django.core.management.base import BaseCommand
from django.db.models import Q
from chat.models import Conversation, Message


class Command(BaseCommand):
    help = 'Merge duplicate conversations between same users'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🔍 Searching for duplicate conversations...'))
        
        all_convos = Conversation.objects.all()
        processed = set()
        merged_count = 0
        
        for convo in all_convos:
            if convo.id in processed:
                continue
                
            # Find duplicate (conversation with same users but swapped roles)
            duplicate = Conversation.objects.filter(
                Q(farmer=convo.officer) & Q(officer=convo.farmer)
            ).exclude(id=convo.id).first()
            
            if duplicate:
                self.stdout.write(
                    self.style.WARNING(
                        f'Found duplicate: Convo #{convo.id} (F={convo.farmer_id}, O={convo.officer_id}) '
                        f'<-> Convo #{duplicate.id} (F={duplicate.farmer_id}, O={duplicate.officer_id})'
                    )
                )
                
                # Keep the older conversation (lower ID)
                keep_convo = convo if convo.id < duplicate.id else duplicate
                delete_convo = duplicate if convo.id < duplicate.id else convo
                
                # Count messages before merge
                keep_msg_count = keep_convo.messages.count()
                delete_msg_count = delete_convo.messages.count()
                
                self.stdout.write(f'  📦 Convo #{keep_convo.id} has {keep_msg_count} messages')
                self.stdout.write(f'  📦 Convo #{delete_convo.id} has {delete_msg_count} messages')
                
                # Move all messages from duplicate to the kept conversation
                moved = Message.objects.filter(conversation=delete_convo).update(conversation=keep_convo)
                
                self.stdout.write(self.style.SUCCESS(f'  ✅ Moved {moved} messages to conversation #{keep_convo.id}'))
                
                # Delete the duplicate conversation
                delete_convo.delete()
                self.stdout.write(self.style.SUCCESS(f'  ✅ Deleted conversation #{delete_convo.id}'))
                
                # Mark both as processed
                processed.add(convo.id)
                processed.add(duplicate.id)
                merged_count += 1
                
                # Verify the merge
                final_count = keep_convo.messages.count()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  🎉 Conversation #{keep_convo.id} now has {final_count} messages '
                        f'(expected {keep_msg_count + delete_msg_count})'
                    )
                )
                self.stdout.write('')
        
        if merged_count == 0:
            self.stdout.write(self.style.SUCCESS('✅ No duplicate conversations found!'))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Successfully merged {merged_count} duplicate conversation(s)!'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    '\n💡 Tip: Restart your Django server and mobile apps to see the changes.'
                )
            )