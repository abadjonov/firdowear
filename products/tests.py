from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils.translation import override

from .models import Category, Product, SizeType


@override_settings(LANGUAGE_CODE="uz")
class CategoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root = Category.objects.create(name="Ustki kiyim", slug="ustki")
        cls.child = Category.objects.create(name="Hoodie", slug="hoodie", parent=cls.root)
        cls.leaf = Category.objects.create(name="Futbolki", slug="futbolki")

    def assert_parent_invalid(self, category):
        with self.assertRaises(ValidationError) as error:
            category.full_clean()
        self.assertIn("parent", error.exception.message_dict)

    def test_valid_root_and_child(self):
        self.root.full_clean()
        self.child.full_clean()
        self.leaf.full_clean()

    def test_labels(self):
        self.assertEqual(str(self.root), "Ustki kiyim")
        self.assertEqual(str(self.child), "Ustki kiyim → Hoodie")

    def test_self_parent_label_does_not_recurse(self):
        Category.objects.filter(pk=self.leaf.pk).update(parent_id=self.leaf.pk)
        self.assertEqual(str(Category.objects.get(pk=self.leaf.pk)), "Futbolki → Futbolki")

    def test_cycle_labels_do_not_recurse(self):
        Category.objects.filter(pk=self.root.pk).update(parent_id=self.child.pk)
        self.assertEqual(str(Category.objects.get(pk=self.root.pk)), "Hoodie → Ustki kiyim")
        self.assertEqual(str(Category.objects.get(pk=self.child.pk)), "Ustki kiyim → Hoodie")

    def test_labels_use_translated_parent_name(self):
        self.root.name_ru = "Верхняя одежда"
        self.root.save()
        self.child.name_ru = "Худи"
        with override("ru"):
            self.assertEqual(str(self.child), "Верхняя одежда → Худи")

    def test_self_parent_rejected(self):
        self.leaf.parent = self.leaf
        self.assert_parent_invalid(self.leaf)

    def test_third_level_rejected(self):
        self.assert_parent_invalid(Category(name="Third", slug="third", parent=self.child))

    def test_cycle_rejected(self):
        self.root.parent = self.child
        self.assert_parent_invalid(self.root)

    def test_parent_in_existing_cycle_rejected(self):
        Category.objects.filter(pk=self.root.pk).update(parent_id=self.child.pk)
        self.leaf.parent = self.root
        self.assert_parent_invalid(self.leaf)

    def test_moving_parent_with_children_rejected(self):
        self.root.parent = self.leaf
        self.assert_parent_invalid(self.root)

    def test_moving_leaf_to_another_root_allowed(self):
        self.child.parent = self.leaf
        self.child.full_clean()

    def test_promoting_child_to_root_allowed(self):
        self.child.parent = None
        self.child.full_clean()

    def test_missing_parent_reports_validation_error(self):
        self.leaf.parent_id = 999999
        self.assert_parent_invalid(self.leaf)

    def test_product_accepts_only_leaf_categories(self):
        size_type = SizeType.objects.create(code="letter", name="Letter")
        for category in (self.leaf, self.child, self.root):
            with self.subTest(category=category):
                product = Product(
                    name="Test", slug="test", category=category,
                    size_type=size_type, price=50000,
                )
                if category == self.root:
                    with self.assertRaises(ValidationError) as error:
                        product.full_clean()
                    self.assertIn("category", error.exception.message_dict)
                else:
                    product.full_clean()


@override_settings(
    LANGUAGE_CODE="uz",
    SECURE_SSL_REDIRECT=False,
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)
class CategoryAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser("admin", password="test-password")
        cls.root = Category.objects.create(name="Ustki kiyim", slug="ustki")
        cls.child = Category.objects.create(name="Hoodie", slug="hoodie", parent=cls.root)
        cls.leaf = Category.objects.create(name="Futbolki", slug="futbolki")
        cls.size_type = SizeType.objects.create(code="letter", name="Letter")

    def setUp(self):
        self.client.force_login(self.user)

    def test_changelist_and_change_page_render_with_corrupt_data(self):
        Category.objects.filter(pk=self.leaf.pk).update(parent_id=self.leaf.pk)
        Category.objects.filter(pk=self.root.pk).update(parent_id=self.child.pk)
        for url in (
            reverse("admin:products_category_changelist"),
            reverse("admin:products_category_change", args=[self.leaf.pk]),
            reverse("admin:products_category_add"),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_parent_choices_on_add(self):
        response = self.client.get(reverse("admin:products_category_add"))
        choices = response.context["adminform"].form.fields["parent"].queryset
        self.assertSetEqual(set(choices), {self.root, self.leaf})

    def test_parent_choices_on_change_exclude_self(self):
        for category, expected in (
            (self.root, {self.leaf}),
            (self.leaf, {self.root}),
            (self.child, {self.root, self.leaf}),
        ):
            with self.subTest(category=category):
                response = self.client.get(reverse("admin:products_category_change", args=[category.pk]))
                choices = response.context["adminform"].form.fields["parent"].queryset
                self.assertSetEqual(set(choices), expected)

    def test_invalid_parent_posts_show_field_error_without_saving(self):
        for category, parent in (
            (self.leaf, self.leaf),  # self-parent
            (self.leaf, self.child),  # third level
            (self.root, self.child),  # cycle
            (self.root, self.leaf),  # moving a subtree creates a third level
        ):
            with self.subTest(category=category, parent=parent):
                response = self.client.post(
                    reverse("admin:products_category_change", args=[category.pk]),
                    {"name_uz": category.name, "slug": category.slug,
                     "parent": parent.pk, "sort_order": 0, "is_active": "on"},
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn("parent", response.context["adminform"].form.errors)
                category.refresh_from_db()
                self.assertIsNone(category.parent_id)

    def test_self_parent_can_be_repaired_in_admin(self):
        Category.objects.filter(pk=self.leaf.pk).update(parent_id=self.leaf.pk)
        response = self.client.post(
            reverse("admin:products_category_change", args=[self.leaf.pk]),
            {"name_uz": self.leaf.name, "slug": self.leaf.slug,
             "parent": "", "sort_order": 0, "is_active": "on"},
        )
        self.assertEqual(response.status_code, 302)
        self.leaf.refresh_from_db()
        self.assertIsNone(self.leaf.parent_id)

    def test_product_add_and_change_offer_root_and_child_leaves(self):
        product = Product.objects.create(
            name="Test", slug="test", category=self.leaf,
            size_type=self.size_type, price=50000,
        )
        for url in (
            reverse("admin:products_product_add"),
            reverse("admin:products_product_change", args=[product.pk]),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                form = response.context["adminform"].form
                self.assertSetEqual(set(form.fields["category"].queryset), {self.leaf, self.child})

    def test_russian_product_help_text_describes_leaf_categories(self):
        response = self.client.get(
            reverse("admin:products_product_add"), HTTP_ACCEPT_LANGUAGE="ru",
        )
        self.assertContains(response, "Только категория без подкатегорий (1-й или 2-й уровень)")

    def test_product_admin_form_accepts_root_leaf(self):
        response = self.client.get(reverse("admin:products_product_add"))
        form_class = type(response.context["adminform"].form)
        form = form_class(data={
            "name_uz": "Test", "slug": "test", "category": self.leaf.pk,
            "size_type": self.size_type.pk, "price": 50000, "season": "all",
        })
        self.assertTrue(form.is_valid(), form.errors)
        product = form.save()
        self.assertEqual(product.category, self.leaf)


class CategoryMigrationTests(TransactionTestCase):
    migrate_from = [("products", "0002_image_webp_variants")]
    migrate_to = [("products", "0003_category_fix")]

    def test_migration_repairs_self_parent_and_preserves_other_data(self):
        executor = MigrationExecutor(connection)
        # Always restore the full schema, including if an assertion fails.
        self.addCleanup(self.restore_schema)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        OldCategory = old_apps.get_model("products", "Category")
        OldSizeType = old_apps.get_model("products", "SizeType")
        OldProduct = old_apps.get_model("products", "Product")
        root = OldCategory.objects.create(name="Ustki kiyim", slug="ustki")
        child = OldCategory.objects.create(name="Hoodie", slug="hoodie", parent=root)
        broken = OldCategory.objects.create(name="Futbolki", slug="futbolki")
        OldCategory.objects.filter(pk=broken.pk).update(parent_id=broken.pk)
        size_type = OldSizeType.objects.create(code="letter", name="Letter")
        product = OldProduct.objects.create(
            name="Test", slug="test", category=broken, size_type=size_type, price=50000,
        )

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        apps = executor.loader.project_state(self.migrate_to).apps
        NewCategory = apps.get_model("products", "Category")
        repaired = NewCategory.objects.get(pk=broken.pk)
        self.assertIsNone(repaired.parent_id)
        self.assertEqual(repaired.name, "Futbolki")
        self.assertEqual(NewCategory.objects.count(), 3)
        self.assertIsNone(NewCategory.objects.get(pk=root.pk).parent_id)
        self.assertEqual(NewCategory.objects.get(pk=child.pk).parent_id, root.pk)
        self.assertEqual(apps.get_model("products", "Product").objects.get(pk=product.pk).category_id, broken.pk)
        self.assertEqual(
            apps.get_model("products", "Product")._meta.get_field("category").get_limit_choices_to(),
            {"children__isnull": True},
        )

        # Rolling back and reapplying is safe; it never restores the corrupt link.
        executor.migrate(self.migrate_from)
        self.assertIsNone(OldCategory.objects.get(pk=broken.pk).parent_id)
        MigrationExecutor(connection).migrate(self.migrate_to)
        self.assertIsNone(NewCategory.objects.get(pk=broken.pk).parent_id)

    def restore_schema(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
