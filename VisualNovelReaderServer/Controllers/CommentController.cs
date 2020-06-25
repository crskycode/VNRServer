using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices.ComTypes;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Cors;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Microsoft.VisualStudio.Web.CodeGeneration;
using SQLitePCL;
using VisualNovelReaderServer.Data;
using VisualNovelReaderServer.Models;

namespace VisualNovelReaderServer.Controllers
{
    [Route("api/[controller]")]
    [EnableCors]
    [ApiController]
    public class CommentController : ControllerBase
    {
        private readonly ILogger<CommentController> _logger;
        private readonly MainDbContext _dbContext;

        public CommentController(ILogger<CommentController> logger, MainDbContext dbContext)
        {
            _logger = logger;
            _dbContext = dbContext;
        }

        [HttpPost("submit")]
        public async Task<ActionResult<CommentSubmitResult>> Submit(CommentSubmitParams @params)
        {
            User user = await _dbContext.User
                .Where(it => it.Username == @params.Username && it.Password == @params.Password)
                .FirstOrDefaultAsync();

            if (user == null)
                return Unauthorized();

            user.AccessTime = DateTime.UtcNow;

            Game game = null;

            // Support query by MD5
            if (@params.GameMd5 != null && @params.GameMd5.Length == 32)
            {
                game = await _dbContext.Game
                    .Where(it => it.Md5 == @params.GameMd5)
                    .FirstOrDefaultAsync();
            }
            else
            {
                if (@params.GameId == null)
                    return NotFound();

                game = await _dbContext.Game
                    .Where(it => it.Id == @params.GameId)
                    .FirstOrDefaultAsync();
            }

            if (game == null)
                return NotFound();

            Comment comment = new Comment
            {
                GameId = (int)@params.GameId,
                GameItemId = game.GameItemId,
                Context = new Context
                {
                    Hash = @params.Context.Hash,
                    Size = @params.Context.Size,
                    Content = @params.Context.Content
                },
                Type = @params.Type,
                Language = @params.Language,
                Text = @params.Text,
                Disabled = @params.Disabled,
                Locked = @params.Locked,
                Deleted = @params.Deleted,
                CreatorId = user.Id,
                CreationComment = @params.CreationComment,
                CreationTime = DateTime.UtcNow,
                EditorId = user.Id,
                RevisionComment = @params.RevisionComment,
                RevisionTime = DateTime.UtcNow
            };

            _dbContext.Comment.Add(comment);

            await _dbContext.SaveChangesAsync();

            return new CommentSubmitResult { Id = comment.Id };
        }

        [HttpPost("query")]
        public async Task<ActionResult<IEnumerable<CommentResultData>>> Query(CommentQueryParams @params)
        {
            // Support query by MD5
            if (@params.GameMd5 != null && @params.GameMd5.Length == 32)
            {
                Game game = await _dbContext.Game
                    .Where(it => it.Md5 == @params.GameMd5)
                    .FirstOrDefaultAsync();

                if (game == null)
                    return NotFound();

                @params.GameId = game.Id;
            }

            if (@params.GameId == null)
                return BadRequest();

            return await _dbContext.Comment
                .Where(it => it.GameId == @params.GameId && it.Deleted == false)
                .Select(it => new CommentResultData
                {
                    Id = it.Id,
                    GameId = it.GameId,
                    GameItemId = it.GameItemId,
                    Context = new ContextResultData
                    {
                        Hash = it.Context.Hash,
                        Size = it.Context.Size,
                        Content = it.Context.Content
                    },
                    Type = it.Type,
                    Language = it.Language,
                    Text = it.Text,
                    Disabled = it.Disabled,
                    Locked = it.Locked,
                    Liked = it.Liked,
                    Disliked = it.Disliked,
                    CreatorId = it.CreatorId,
                    CreationComment = it.CreationComment,
                    CreationTime = it.CreationTime.ToUnixTimeSeconds(),
                    EditorId = it.EditorId,
                    RevisionComment = it.RevisionComment,
                    RevisionTime = it.RevisionTime.ToUnixTimeSeconds()
                }).ToArrayAsync();
        }

        [HttpPost("update")]
        public async Task<ActionResult<CommentUpdateResult>> Update(CommentUpdateParams @params)
        {
            User user = await _dbContext.User
                .Where(it => it.Username == @params.Username && it.Password == @params.Password)
                .FirstOrDefaultAsync();

            if (user == null)
                return Unauthorized();

            user.AccessTime = DateTime.UtcNow;

            Comment comment = await _dbContext.Comment
                .Where(it => it.Id == @params.Id)
                .FirstOrDefaultAsync();

            if (comment == null)
                return NotFound();

            if (user.Id != comment.CreatorId)
                return Unauthorized();

            if (@params.Context != null)
            {
                if (@params.Context.Hash != null)
                    comment.Context.Hash = @params.Context.Hash;
                if (@params.Context.Size != null)
                    comment.Context.Size = (int)@params.Context.Size;
                if (@params.Context.Content != null)
                    comment.Context.Content = @params.Context.Content;
            }
            if (@params.Type != null)
                comment.Type = @params.Type;
            if (@params.Language != null)
                comment.Language = @params.Language;
            if (@params.Text != null)
                comment.Text = @params.Text;
            if (@params.Disabled != null)
                comment.Disabled = (bool)@params.Disabled;
            if (@params.Locked != null)
                comment.Locked = (bool)@params.Locked;
            if (@params.Deleted != null)
                comment.Deleted = (bool)@params.Deleted;
            if (@params.Liked != null)
                comment.Liked = (int)@params.Liked;
            if (@params.Disliked != null)
                comment.Disliked = (int)@params.Disliked;
            if (@params.CreationComment != null)
                comment.CreationComment = @params.CreationComment;
            if (@params.RevisionComment != null)
                comment.RevisionComment = @params.RevisionComment;

            comment.EditorId = user.Id;
            comment.RevisionTime = DateTime.UtcNow;

            await _dbContext.SaveChangesAsync();

            return new CommentUpdateResult { Id = comment.Id };
        }
    }
}
