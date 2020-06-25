using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Threading.Tasks;

namespace VisualNovelReaderServer.Models
{
    public class UserInfoResult
    {
        public int Id { get; set; }
        public string Username { get; set; }
        public string Language { get; set; }
        public string Gender { get; set; }
        public string Avatar { get; set; }
        public string HomePage { get; set; }
        public string Color { get; set; }
    }

    public class UserRegisterParams
    {
        [Required]
        public string Username { get; set; }
        [Required]
        public string Password { get; set; }
        [Required]
        public string Email { get; set; }
    }

    public class UserLoginParams
    {
        [Required]
        public string Username { get; set; }
        [Required]
        public string Password { get; set; }
    }

    public class UserUpdateParams
    {
        [Required]
        public string Username { get; set; }
        [Required]
        public string Password { get; set; }

        public string Language { get; set; }
        public string Gender { get; set; }
        public string Avatar { get; set; }
        public string HomePage { get; set; }
        public string Color { get; set; }
    }
}
