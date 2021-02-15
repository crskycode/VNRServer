using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Cors;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using VisualNovelReaderServer.Data;
using VisualNovelReaderServer.Models;

namespace VisualNovelReaderServer.Controllers
{
    [Route("api/[controller]")]
    [EnableCors]
    [ApiController]
    public class TermController : ControllerBase
    {
        private readonly ILogger<TermController> _logger;
        private readonly MainDbContext _dbContext;

        public TermController(ILogger<TermController> logger, MainDbContext dbContext)
        {
            _logger = logger;
            _dbContext = dbContext;
        }

        [HttpPost("submit")]
        public async Task<ActionResult<TermSubmitResult>> Submit(TermSubmitParams @params)
        {
            User user = await _dbContext.User
                .Where(it => it.Username == @params.Username && it.Password == @params.Password)
                .FirstOrDefaultAsync();

            if (user == null)
                return Unauthorized();

            user.AccessTime = DateTime.UtcNow;

            Term term = new Term
            {
                FromLanguage = @params.FromLanguage,
                ToLanguage = @params.ToLanguage,
                Type = @params.Type,
                Translators = @params.Translators,
                ContextType = @params.ContextType,
                GameId = @params.GameId,
                IsSpecial = @params.IsSpecial,
                IsPrivate = @params.IsPrivate,
                IsHentai = @params.IsHentai,
                IsRegex = @params.IsRegex,
                IsPhrase = @params.IsPhrase,
                IgnoreCase = @params.IgnoreCase,
                Disabled = @params.Disabled,
                Deleted = @params.Deleted,
                Priority = @params.Priority,
                Role = @params.Role,
                Pattern = @params.Pattern,
                Text = @params.Text,
                Ruby = @params.Ruby,
                CreatorId = user.Id,
                CreationComment = @params.CreationComment,
                CreationTime = DateTime.UtcNow,
                RevisionComment = @params.RevisionComment,
            };

            _dbContext.Term.Add(term);

            await _dbContext.SaveChangesAsync();

            return new TermSubmitResult { Id = term.Id };
        }

        [HttpPost("query")]
        public async Task<ActionResult<TermQueryResult>> Query(TermQueryParams @params)
        {
            User user = await _dbContext.User
                .Where(it => it.Username == @params.Username && it.Password == @params.Password)
                .FirstOrDefaultAsync();

            if (user == null)
                return Unauthorized();

            user.AccessTime = DateTime.UtcNow;

            await _dbContext.SaveChangesAsync();

            var terms = _dbContext.Term
                .Where(it => it.Deleted == false)
                .OrderByDescending(it => it.CreationTime);

            return new TermQueryResult
            {
                Timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds(),

                Terms = await terms.Select(it => new TermResultData
                {
                    Id = it.Id,
                    FromLanguage = it.FromLanguage,
                    ToLanguage = it.ToLanguage,
                    Type = it.Type,
                    Translators = it.Translators,
                    ContextType = it.ContextType,
                    GameId = it.GameId,
                    IsSpecial = it.IsSpecial,
                    IsPrivate = it.IsPrivate,
                    IsHentai = it.IsHentai,
                    IsRegex = it.IsRegex,
                    IsPhrase = it.IsPhrase,
                    IgnoreCase = it.IgnoreCase,
                    Disabled = it.Disabled,
                    Priority = it.Priority,
                    Role = it.Role,
                    Pattern = it.Pattern,
                    Text = it.Text,
                    Ruby = it.Ruby,
                    CreatorId = it.CreatorId,
                    CreationComment = it.CreationComment,
                    CreationTime = it.CreationTime.ToUnixTimeSeconds(),
                    EditorId = it.EditorId,
                    RevisionComment = it.RevisionComment,
                    RevisionTime = it.RevisionTime.ToUnixTimeSeconds()
                }).ToArrayAsync()
            };
        }

        [HttpPost("update")]
        public async Task<ActionResult<TermUpdateResult>> Update(TermUpdateParams @params)
        {
            User user = await _dbContext.User
                .Where(it => it.Username == @params.Username && it.Password == @params.Password)
                .FirstOrDefaultAsync();

            if (user == null)
                return Unauthorized();

            user.AccessTime = DateTime.UtcNow;

            Term term = await _dbContext.Term
                .Where(it => it.Id == @params.Id && it.Deleted == false)
                .FirstOrDefaultAsync();

            if (term == null)
                return NotFound();

            if (user.Id != term.CreatorId)
                return Unauthorized();

            // Perhaps the reflection can be used to simplify the code.

            if (@params.FromLanguage != null)
                term.FromLanguage = @params.FromLanguage;
            if (@params.ToLanguage != null)
                term.ToLanguage = @params.ToLanguage;
            if (@params.Type != null)
                term.Type = @params.Type;
            if (@params.Translators != null)
                term.Translators = @params.Translators;
            if (@params.ContextType != null)
                term.ContextType = @params.ContextType;
            if (@params.GameId != null)
                term.GameId = (int)@params.GameId == 0 ? null : (int)@params.GameId;
            if (@params.IsSpecial != null)
                term.IsSpecial = (bool)@params.IsSpecial;
            if (@params.IsPrivate != null)
                term.IsPrivate = (bool)@params.IsPrivate;
            if (@params.IsHentai != null)
                term.IsHentai = (bool)@params.IsHentai;
            if (@params.IsRegex != null)
                term.IsRegex = (bool)@params.IsRegex;
            if (@params.IsPhrase != null)
                term.IsPhrase = (bool)@params.IsPhrase;
            if (@params.IgnoreCase != null)
                term.IgnoreCase = (bool)@params.IgnoreCase;
            if (@params.Disabled != null)
                term.Disabled = (bool)@params.Disabled;
            if (@params.Deleted != null)
                term.Deleted = (bool)@params.Deleted;   // Just mark it deleted.
            if (@params.Priority != null)
                term.Priority = (int)@params.Priority;
            if (@params.Role != null)
                term.Role = @params.Role;
            if (@params.Pattern != null)
                term.Pattern = @params.Pattern;
            if (@params.Text != null)
                term.Text = @params.Text;
            if (@params.Ruby != null)
                term.Ruby = @params.Ruby;
            if (@params.RevisionComment != null)
                term.RevisionComment = @params.RevisionComment;

            term.EditorId = user.Id;
            term.RevisionTime = DateTime.UtcNow;

            await _dbContext.SaveChangesAsync();

            return new TermUpdateResult { Id = term.Id };
        }
    }
}
