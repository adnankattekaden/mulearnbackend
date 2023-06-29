from django.db.models import Sum, F
from rest_framework import serializers

from db.organization import UserOrganizationLink
from db.task import UserLvlLink, TotalKarma


class UserOrgSerializer(serializers.ModelSerializer):
    fullname = serializers.ReadOnlyField(source="user.fullname")
    muid = serializers.ReadOnlyField(source="user.mu_id")
    karma = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()

    class Meta:
        model = TotalKarma
        fields = ["fullname", "karma", "muid", "rank", "level"]

    def get_karma(self, obj):
        return obj.user.total_karma_user.karma or 0

    def get_rank(self, obj):
        rank = TotalKarma.objects.filter(
            user__total_karma_user__isnull=False
        ).annotate(
            rank=F('user__total_karma_user__karma')
        ).order_by('-rank').values_list('rank', flat=True)

        ranks = {karma: i + 1 for i, karma in enumerate(rank)}
        return ranks.get(obj.user.total_karma_user.karma, None)

    def get_level(self, obj):
        user_level_link = UserLvlLink.objects.filter(user=obj.user).first()
        if user_level_link:
            return user_level_link.level.name
        return None


class CollegeSerializer(serializers.ModelSerializer):
    collegeName = serializers.ReadOnlyField(source="org.title")
    campusCode = serializers.ReadOnlyField(source="org.code")
    campusZone = serializers.ReadOnlyField(source="org.district.zone.name")
    campusLead = serializers.ReadOnlyField(source="user.fullname")
    totalKarma = serializers.SerializerMethodField()
    totalMembers = serializers.SerializerMethodField()
    activeMembers = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()

    class Meta:
        model = UserOrganizationLink
        fields = ["collegeName", "campusLead", "campusCode",
                  "campusZone", "totalKarma", "totalMembers", "activeMembers", "rank"]

    def get_totalKarma(self, obj):
        karma = obj.org.user_organization_link_org_id.filter(verified=True).aggregate(
            total_karma=Sum('user__total_karma_user__karma'))
        return karma['total_karma'] or 0

    def get_totalMembers(self, obj):
        return obj.org.user_organization_link_org_id.count()

    def get_activeMembers(self, obj):
        return obj.org.user_organization_link_org_id.filter(verified=True, user__active=True).count()

    def get_rank(self, obj):
        rank = UserOrganizationLink.objects.filter(
            org__org_type="College", verified=True, user__total_karma_user__isnull=False
        ).annotate(
            total_karma=Sum('user__total_karma_user__karma')
        ).order_by('-total_karma').values_list('total_karma', flat=True)

        colleges = {karma: i + 1 for i, karma in enumerate(rank)}
        return colleges.get(obj.user.total_karma_user.karma, None)
