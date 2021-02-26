import hashlib
import uuid

from django.db import models

from .fields import GooglePublicImageField


def delete_image(sender, instance: "Image", **kwargs) -> None:
    """ Delete the underlying image of the image model baseclass """
    try:
        getattr(instance.image, "file")
        instance.image.delete(save=False)

    except ValueError:
        # The file may have already been deleted,
        # or never existed at all, in that case ignore it
        pass


class Image(models.Model):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4
    )
    image = models.ImageField(null=True)
    image_hash = models.TextField(null=True)

    class Meta:
        abstract = True

    def _check_image_overwritten_to_none(new, old) -> bool:  # noqa attr self
        # First, check if the current already saved instance,
        # has an image associated with it
        try:
            getattr(old.image, "file")
        except ValueError:
            # If not we already know we are not overwriting an existing
            # profile picture to None
            return False

        # Next, check if the new instance has an image
        try:
            getattr(new.image, "file")
        except ValueError:
            # If not, we know the user wants to overwrite the existing image to None
            # Thus we can return True
            return True

        # If both of these passed, that means that both instances have images
        # so we need to compare them in the next steps.
        # This method is thus falsy
        return False

    def save(self, *args, **kwargs) -> None:
        old_instance = None
        new_instance = self

        try:
            old_instance = UserProfilePicture.objects.get(id=self.id)

        except UserProfilePicture.DoesNotExist:
            # If our lookup does not find an instance,
            # that means that we are currently creating the object
            creating = True

        else:
            creating = False

        if not creating:
            if self._check_image_overwritten_to_none(old_instance):
                old_instance.image.delete(save=False)

        # Create the hash for the file object
        try:
            file = self.image.file  # File wrapper object

            if hasattr(file.file, "getvalue"):
                # file.file is underlying BytesIO file
                file_content = file.file.getvalue()
            else:
                # it may also be a SpooledTemporaryFile,
                # in that case the actual BytesIO object is nested a level deeper
                file_content = file.file._file.getvalue()  # noqa private
            img_hash = hashlib.blake2b(file_content).hexdigest()
            self.image_hash = img_hash

        # This is the case for when there is no image associated
        # with the instance yet
        except ValueError:
            pass

        if not creating:
            try:
                # This instance may have already been created
                # but still not have an image associated with it
                # in that case the below code would break so we need to check,
                # if an image file has already been added to the instance
                hasattr(self.image, "file")

                old_image_hash = old_instance.image_hash
                new_image_hash = new_instance.image_hash

                # If the hashes are not the same,
                # that means that the image has been updated,
                # in that case, we delete the old one
                if not old_image_hash == new_image_hash:
                    old_instance.image.delete(save=False)

            except ValueError:
                # no file bound, just skip the entire process
                pass

        super().save(*args, **kwargs)

    @classmethod
    def __init_subclass__(cls, **kwargs) -> None:
        """
        Connect all of our concrete subclasses,
        to the post delete event of our abstract base class.

        This is so we can automatically delete the related image file,
        in case any model instances get deleted through CASCADE from their parent.
        """
        super().__init_subclass__(**kwargs)

        models.signals.post_delete.connect(  # connect the callback function
            delete_image, sender=cls
        )


def get_user_filename(instance, filename) -> str:
    ext = filename.split(".")[-1]

    # The 'subdirectory' (this is not actually a directory as
    # CloudStorage has a flat namespace) should always have the name
    # of the application namespace it is from
    return f"images/users/profiles/{instance.pk}.{ext}"


class UserProfilePicture(Image):
    image = GooglePublicImageField(
        upload_to=get_user_filename,
        null=True,
    )
    background = models.IntegerField()
    owner = models.OneToOneField(
        to="users.User",
        on_delete=models.CASCADE,
        null=True,
        related_name="profile_picture"
    )


__all__ = ["UserProfilePicture"]
