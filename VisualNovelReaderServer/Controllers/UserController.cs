using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Cors;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Microsoft.VisualBasic;
using VisualNovelReaderServer.Data;
using VisualNovelReaderServer.Models;

namespace VisualNovelReaderServer.Controllers
{
    [Route("api/[controller]")]
    [EnableCors]
    [ApiController]
    public class UserController : ControllerBase
    {
        private readonly ILogger<UserController> _logger;
        private readonly MainDbContext _dbContext;

        public UserController(ILogger<UserController> logger, MainDbContext dbContext)
        {
            _logger = logger;
            _dbContext = dbContext;
        }

        // POST: api/user/register
        [HttpPost("register")]
        public async Task<ActionResult> Register(UserRegisterParams @params)
        {
            User user = await _dbContext.User
                .Where(it => it.Username == @params.Username)
                .FirstOrDefaultAsync();

            if (user != null)
                return BadRequest();    // 用户名已存在

            _dbContext.User.Add(
                new User()
                {
                    Username = @params.Username,
                    Password = @params.Password,
                    Email = @params.Email,
                    CreationTime = DateTime.UtcNow,
                    AccessTime = DateTime.UtcNow,
                    ModifiedTime = DateTime.UtcNow
                });

            await _dbContext.SaveChangesAsync();

            return Ok();
        }

        [HttpPost("login")]
        public async Task<ActionResult<UserInfoResult>> Login(UserLoginParams @params)
        {
            User user = await _dbContext.User
                .Where(it => it.Username == @params.Username && it.Password == @params.Password)
                .FirstOrDefaultAsync();

            if (user == null)
                return Unauthorized();

            _logger.LogInformation("User '{1}' logged in.", user.Username);

            user.AccessTime = DateTime.UtcNow;

            await _dbContext.SaveChangesAsync();

            return new UserInfoResult
            {
                Id = user.Id,
                Username = user.Username,
                Language = user.Language,
                Gender = user.Gender,
                Avatar = user.Avatar,
                HomePage = user.HomePage,
                Color = user.Color
            };
        }

        [HttpPost("all")]
        public async Task<ActionResult<IEnumerable<UserInfoResult>>> QueryAll()
        {
            return await _dbContext.User
                .OrderBy(it => it.Id)
                .Select(it => new UserInfoResult
                {
                    Id = it.Id,
                    Username = it.Username,
                    Language = it.Language,
                    Gender = it.Gender,
                    Avatar = it.Avatar,
                    HomePage = it.HomePage,
                    Color = it.Color
                }).ToArrayAsync();
        }

        [HttpPost("update")]
        public async Task<ActionResult> Update(UserUpdateParams @params)
        {
            User user = await _dbContext.User
                .Where(it => it.Username == @params.Username && it.Password == @params.Password)
                .FirstOrDefaultAsync();

            if (user == null)
                return Unauthorized();

            user.AccessTime = DateTime.UtcNow;
            user.ModifiedTime = DateTime.UtcNow;

            if (@params.Language != null)
                user.Language = @params.Language;
            if (@params.Gender != null)
                user.Gender = @params.Gender;
            if (@params.Avatar != null)
                user.Avatar = @params.Avatar;
            if (@params.HomePage != null)
                user.HomePage = @params.HomePage;
            if (@params.Color != null)
                user.Color = @params.Color;

            await _dbContext.SaveChangesAsync();

            return Ok();
        }
    }
}
